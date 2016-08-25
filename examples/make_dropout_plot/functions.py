import pandas as pd
from .api import fetch_objects
from .api import fetch_objects_by_id
from .api import fetch_objects_by_pk
import time
import matplotlib as plt
plt.use("pgf")
pgf_with_custom_preamble = {
    "text.usetex": True,
    "pgf.preamble": [
        r"\usepackage{hyperref}"
        ]
}
import seaborn as sns
from pylab import *
plt.rcParams.update(pgf_with_custom_preamble)


def get_unix_date(date):
    timestamp = time.mktime(datetime.datetime.strptime(date.split('+')[0], "%Y-%m-%dT%H:%M:%SZ").timetuple())
    return timestamp


def get_drop_out_plot(course_id):
    course = fetch_objects_by_id('courses', course_id)[0]
    sections = fetch_objects('sections', id=course['sections'])

    unit_ids = [unit for section in sections for unit in section['units']]
    units = fetch_objects('units', id=unit_ids)

    lesson_ids = [unit['lesson'] for unit in units]
    lessons = fetch_objects('lessons', id=lesson_ids)

    step_ids = [step for lesson in lessons for step in lesson['steps']]
    steps = fetch_objects('steps', id=step_ids)
    step_id = [step['id'] for step in steps]
    step_position = [step['position'] for step in steps]
    step_type = [step["block"]["name"]for step in steps]
    step_lesson = [step["lesson"] for step in steps]
    step_correct_ratio = [step["correct_ratio"] for step in steps]

    course_structure = pd.DataFrame({"course_id": course_id,
                                     "lesson_id": step_lesson,
                                     "step_id": step_id,
                                     "step_position": step_position,
                                     "step_type": step_type,
                                     "step_correct_ratio": step_correct_ratio})

    module_position = [[section["position"]] * len(section["units"]) for section in sections]
    module_position = [value for small_list in module_position for value in small_list]

    module_id = [[section["id"]] * len(section["units"]) for section in sections]
    module_id = [value for small_list in module_id for value in small_list]

    module_hard_deadline = [[section["hard_deadline"]] * len(section["units"]) for section in sections]
    module_hard_deadline = [value for small_list in module_hard_deadline for value in small_list]

    module_begin_date = [[section["begin_date"]] * len(section["units"]) for section in sections]
    module_begin_date = [value for small_list in module_begin_date for value in small_list]

    lesson_position = [unit['position'] for unit in units]

    module_structure = pd.DataFrame({"lesson_id": lesson_ids,
                                     "lesson_position": lesson_position,
                                     "module_id": module_id,
                                     "module_position": module_position,
                                     "module_hard_deadline": module_hard_deadline,
                                     "begin_date": module_begin_date})

    course_structure = course_structure.merge(module_structure)
    course_structure = course_structure.query("step_type != 'video' & step_type != 'text'")
    course_structure = course_structure.sort_values(["module_position", "lesson_position", "step_position"])

    if not pd.isnull(course_structure.module_hard_deadline).any():
        course_structure["module_hard_deadline"] = list(map(get_unix_date, course_structure.module_hard_deadline))

    if not pd.isnull(course_structure.begin_date).any():
        course_structure["begin_date"] = list(map(get_unix_date, course_structure.begin_date))

    course = fetch_objects_by_id('courses', course_id)[0]
    course_name = course["title"]
    certificate_threshold = course["certificate_regular_threshold"]
    # number_of_weeks = len(course["sections"])
    begin_date = get_unix_date(course["begin_date"])
    last_deadline = get_unix_date(course["last_deadline"])
    course_teachers = course["instructors"]
    course_testers = fetch_objects_by_pk("groups", course["testers_group"])[0]["users"]
    users_to_delete = course_teachers + course_testers

    grades = fetch_objects('course-grades', course=course_id)
    learners = pd.DataFrame({"user_id": [user["user"] for user in grades],
                             "total": [user["score"] for user in grades],
                             "data_joined": [user["date_joined"] for user in grades]})

    learners = learners.query("not(user_id in @course_testers)")
    learners = learners.query("total > 0 and total < @certificate_threshold")

    if not pd.isnull(learners.data_joined).any():
        learners["data_joined_unix"] = list(map(get_unix_date, learners.data_joined.values))

    course_submissions = pd.DataFrame()
    for learner in learners.user_id:
        step_data = pd.DataFrame()
        for step in course_structure.step_id:
            step_submissions = fetch_objects('submissions', step=step, user=learner)
            submissions_data = pd.DataFrame()
            for submission in step_submissions:
                current_submission = pd.DataFrame({"step_id": [step],
                                                   "user_id": [learner],
                                                   "submission_time": submission["time"],
                                                   "status":  submission["status"]})
                submissions_data = submissions_data.append(current_submission)
            step_data = step_data.append(submissions_data)
        course_submissions = course_submissions.append(step_data)

    course_submissions["submission_time_unix"] = list(map(get_unix_date, course_submissions.submission_time))

    course_submissions = course_submissions.query("@begin_date < submission_time_unix < @last_deadline")

    idx_grouped = course_submissions.groupby(['user_id'])['submission_time_unix']
    idx = idx_grouped.transform(max) == course_submissions['submission_time_unix']

    last_submissions = course_submissions[idx].query("status == 'wrong'")

    step_stats = last_submissions.groupby("step_id", as_index=False).count()
    step_stats = step_stats.merge(course_structure[["step_id", "step_correct_ratio"]])
    step_stats["Difficulty"] = 1 - step_stats.step_correct_ratio

    # make a final plot
    x = np.arange(1, len(step_stats.step_id) + 1)
    labels = []
    for i in step_stats.step_id.values:
        step_data = course_structure.query("step_id == @i")
        address = 'https://stepic.org/{course_id}/{lesson_id}/{step_position}'. \
            format(course_id=course_id,
                   lesson_id=step_data.lesson_id.item(),
                   step_position=step_data.step_position.item())

        label = '\href{{{address}}}{{{step_id}}}'.format(address=address, step_id=step_data.step_id.item())
        labels.append(label)

    label_size = 9
    plt.rcParams['xtick.labelsize'] = label_size
    sns.set_style("white")
    fig, ax1 = plt.subplots(figsize=(20, 10))
    ax1.tick_params(axis='x', which='major', pad=5)
    ax1.grid(zorder=0)
    ax1.bar(x, step_stats.Difficulty, align='center')
    ax1.set_xlabel('Step_id')
    plt.xticks(x, labels, rotation=85)

    # Make the y-axis label and tick labels match the line color.
    ax1.set_ylabel('Difficulty', color='b')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax2 = ax1.twinx()
    ax2.bar(x, step_stats.user_id, color='r', alpha=0.5, align='center', width=0.5)
    ax2.set_ylabel('Users left', color='r')

    for tl in ax2.get_yticklabels():
        tl.set_color('r')

    plt.title('{course_name} {id}\n'.format(course_name=course_name, id=course_id))

    plt.gcf().subplots_adjust(bottom=0.30)

    figtext(.02, 0.2, "На данном графике каждый шаг (step_id) характеризается двумя параметрами. \
                       Обратите внимание, если вы нажмете на id шага, то перейдете на этот шаг в курсе.")
    figtext(.02, 0.18,
            "Красные столбики поуже Users left - число человек, покинувших курс на данном шаге. \
             Точное число отложено по правой вертикальной оси.", color="red")

    figtext(.02, 0.16,
            "Синие столбики Difficulty - сложность шага (1 - success rate).\
            Точное значение отложено по левой вертикальной оси.", color="blue")

    fig.savefig('{course_name} {id}.pdf'.format(course_name=course_name, id=course_id))

