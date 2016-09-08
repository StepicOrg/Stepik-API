import os
import numpy as np
import pandas as pd
import ast

import datetime
import csv

from library.api import get_object, get_api_request, get_object_by_pk, API_BASE_URL
from library.report import get_course_structure




def generate_latex_report(course_id, directory):

    course_info = get_object_by_pk('courses', course_id)

    course_title = course_info['title']
    course_url = 'https://stepik.org/course/{}'.format(course_id)

    with open('{}info.tex'.format(directory), 'w') as info_file:
        info_file.write('\\def\\coursetitle{{{}}}\n\\def\\courseurl{{{}}}\n'.format(course_title, course_url))

    course_structure = get_course_structure(course_id)
    course_structure = course_structure[course_structure.step_type == 'choice']
    course_structure.drop(['begin_date', 'end_date', 'soft_deadline',
                           'hard_deadline', 'grading_policy'], axis=1, inplace=True)
    course_structure['step_variation'] = course_structure.groupby(['lesson_id', 'step_position']).cumcount()
    course_structure['step_variation'] += 1

    submissions = get_submissions_by_step_id(course_id, course_structure.step_id.tolist())
    submissions = pd.merge(submissions, course_structure, on='step_id')

    # TODO: add mean response time to item statistics
    submissions['time'] = submissions['submission_time'] - submissions['attempt_time']

    # Item statistics
    item_statistics_filename = 'cache/course-{}-item-statistics.csv'.format(course_id)
    if os.path.isfile(item_statistics_filename):
        item_statistics = pd.read_csv(item_statistics_filename)
    else:
        answers = create_answer_matrix(submissions, 'user_id', 'step_id', 'status',
                                       lambda x: int('wrong' not in x.tolist()), 'submission_time')

        item_statistics = get_item_statistics(answers)
        item_statistics = item_statistics.rename(columns={'item': 'step_id'})
        item_statistics = pd.merge(item_statistics, course_structure, on='step_id')

        item_statistics['step_url'] = item_statistics.apply(process_step_url, axis=1)
        item_statistics['question'] = item_statistics['step_id'].apply(get_question)

        item_statistics = item_statistics.sort_values(['module_position', 'lesson_position',
                                                       'step_position', 'step_id'])
        item_statistics.to_csv(item_statistics_filename, index=False)

    # Options analysis
    option_statistics_filename = 'cache/course-{}-option-statistics.csv'.format(course_id)
    if os.path.isfile(option_statistics_filename):
        option_statistics = pd.read_csv(option_statistics_filename)
    else:
        option_statistics = pd.DataFrame(columns=['step_id',
                                                  'is_multiple',
                                                  'option_id',
                                                  'option_name',
                                                  'clue',
                                                  'difficulty',
                                                  'discrimination'])
        option_statistics[['step_id', 'option_id']] = option_statistics[['step_id', 'option_id']].astype(int)
        for step_id in submissions.step_id.unique():
            print('Option analysis for step_id = ', step_id)
            step_submissions = submissions[submissions.step_id == step_id]

            option_names = get_step_options(step_id)

            step_options = pd.DataFrame(columns=['user_id', 'is_multiple', 'option_id', 'answer', 'clue'])
            for i, row in step_submissions.iterrows():
                try:
                    options = process_options_with_name(row['dataset'], row['reply'], option_names=option_names)
                except(ValueError, KeyError):
                    # cannot process submission
                    continue

                options['user_id'] = row['user_id']
                step_options = step_options.append(options)

            step_answers = create_answer_matrix(step_options, 'user_id', 'option_id', 'answer',
                                                lambda x: int(False not in x.tolist()))

            step_statistics = get_item_statistics(step_answers)
            step_statistics = step_statistics.rename(columns={'item': 'option_id',
                                                              'item_total_corr': 'option_item_corr'})
            step_statistics = pd.merge(step_statistics,
                                       step_options.loc[:, ['option_id', 'clue']].drop_duplicates(),
                                       on='option_id')
            step_statistics = pd.merge(step_statistics, option_names, on='option_id')

            option_statistics = option_statistics.append(step_statistics)

        option_statistics.to_csv('cache/course-{}-option-statistics.csv'.format(course_id), index=False)

    generate_latex_files(item_statistics, option_statistics, directory)


def compile_latex_report(course_id, directory, update=False):
    latex_command = 'pdflatex -synctex=1 -interaction=nonstopmode item_report.tex'

    os.chdir(directory)

    if update:
        os.system('cp -rf ../default/* .')

    # Launch LaTeX three times
    os.system(latex_command)
    os.system(latex_command)
    os.system(latex_command)

    os.system('cp item_report.pdf ../../pdf/course-{}-item-report.pdf'.format(course_id))


def create_answer_matrix(data, user_column, item_column, value_column, aggfunc=np.mean, time_column=None):
    if time_column:
        # select only the first response
        data = data.loc[data.groupby([item_column, user_column])[time_column].idxmin()]
        data = data.drop_duplicates(subset=[item_column, user_column])

    answers = pd.pivot_table(data, values=[value_column], index=[user_column], columns=[item_column], aggfunc=aggfunc)

    if not answers.empty:
        answers = answers[value_column]

    return answers


# TODO: add Cronbach's alpha to item statistics
# see http://stackoverflow.com/questions/20799403/improving-performance-of-cronbach-alpha-code-python-numpy
def get_item_statistics(answers, discrimination_prop=0.3):
    total_people = answers.shape[0]

    n_people = answers.count(axis=0)

    # use mean (not sum) because of NA values
    item_difficulty = 1-answers.mean(axis=0)
    total_score = answers.mean(axis=1)
    item_total_corr = answers.corrwith(total_score)

    n_top_people = int(discrimination_prop*total_people)
    low_performers = total_score.sort_values().index[:n_top_people]
    top_performers = total_score.sort_values().index[-n_top_people:]
    item_discrimination = answers.loc[top_performers].mean(axis=0) - answers.loc[low_performers].mean(axis=0)

    stats = pd.DataFrame({'item': item_difficulty.index,
                          'n_people': n_people,
                          'difficulty': item_difficulty,
                          'item_total_corr': item_total_corr,
                          'discrimination': item_discrimination})
    stats.reset_index(drop=True, inplace=True)
    stats = stats[['item', 'n_people', 'difficulty', 'discrimination', 'item_total_corr']]
    return stats


def process_options(data, clue, reply, option_dict):
    data = ast.literal_eval(data)
    clue = ast.literal_eval(clue)
    reply = ast.literal_eval(reply)['choices']

    is_multiple = data['is_multiple_choice']
    options = data['options']
    answer = [(c == r) for c, r in zip(clue, reply)]

    option_id = []
    for op in options:
        if op in option_dict:
            val = option_dict[op]
        else:
            val = np.nan
        option_id += [val]

    options = pd.DataFrame({'is_multiple': is_multiple,
                            'option_id': option_id,
                            'answer': answer,
                            'clue': clue})
    options = options[['is_multiple', 'option_id', 'answer', 'clue']]

    return options


def process_options_with_name(data, reply, option_names):
    data = ast.literal_eval(data)
    reply = ast.literal_eval(reply)['choices']

    is_multiple = data['is_multiple_choice']
    options = data['options']

    option_id = []
    clue = []
    for op in options:
        if op in option_names.option_name.tolist():
            val = option_names.loc[option_names.option_name == op, 'option_id'].values[0]
            clue_val = option_names.loc[option_names.option_name == op, 'is_correct'].values[0]
        else:
            val = np.nan
            clue_val = np.nan
        option_id += [val]
        clue += [clue_val]

    answer = [(c == r) for c, r in zip(clue, reply)]

    options = pd.DataFrame({'is_multiple': is_multiple,
                            'option_id': option_id,
                            'answer': answer,
                            'clue': clue})
    options = options[['is_multiple', 'option_id', 'answer', 'clue']]

    return options


def get_option_dict(dataset):
    option_set = set()
    for data in dataset:
        options = ast.literal_eval(data)['options']
        option_set |= set(options)

    option_list = sorted(option_set)
    return dict(zip(option_list, range(1, len(option_list)+1)))


def get_question(step_id):
    source = get_object('step-sources', ids=[step_id])

    try:
        question = source[0]['block']['text']
    except:
        question = '\n'

    question = html2latex(question)

    return question


def get_step_options(step_id):
    source = get_object('step-sources', ids=[step_id])

    try:
        options = source[0]['block']['source']['options']
        options = pd.DataFrame(options)
        is_multiple = source[0]['block']['source']['is_multiple_choice']
    except:
        options = pd.DataFrame(columns=['step_id', 'option_id', 'option_name', 'is_correct', 'is_multiple'])
        return options

    options['step_id'] = step_id
    options['is_multiple'] = is_multiple
    options = options.sort_values('text').reset_index()
    options = options.rename(columns={'text': 'option_name'})
    options['option_id'] = options.index + 1
    options = options[['step_id', 'option_id', 'option_name', 'is_correct', 'is_multiple']]

    return options


def get_submissions_by_step_id(course_id, steps, cache=True):

    cached_name = 'cache/course-{}-submissions-full.csv'.format(course_id)

    if cache and os.path.isfile(cached_name):
        csv.field_size_limit(500 * 1024 * 1024)
        with open(cached_name) as csvfile:
            submissions_csv = csv.DictReader(csvfile)
            header = submissions_csv.fieldnames
            rows = []
            while True:
                try:
                    row = next(submissions_csv)
                    rows.append(row)
                except csv.Error as e:
                    # log the problem
                    print('row: ', row)
                    print('file {}, line {}: {}'.format(cached_name, submissions_csv.line_num, e))
                    continue
                except StopIteration:
                    break

        submissions = pd.DataFrame(rows, columns=header)
        submissions['step_id'] = pd.to_numeric(submissions['step_id'], 'coerc')

        submissions = submissions[submissions.step_id.isin(steps)]

        submissions[['submission_id', 'step_id', 'user_id', 'attempt_time', 'submission_time']] = submissions[[
            'submission_id', 'step_id', 'user_id', 'attempt_time', 'submission_time']].astype(int)

        return submissions

    URL_FORMAT = API_BASE_URL+'api/submissions?step={}&page={}'
    header = ['submission_id', 'step_id', 'user_id', 'attempt_time',
              'submission_time', 'status', 'dataset', 'clue', 'reply', 'hint']
    submissions = None
    for step_id in steps:
        page = 1
        request = get_api_request(URL_FORMAT.format(step_id, page))

        if 'meta' not in request:
            # if not success (e.g., error 404), then return an empty list
            res = []
        else:
            # success
            res = pd.DataFrame(request['submissions'])
            attempts = pd.DataFrame(get_object('attempts', ids=res['attempt'].tolist()))
            attempts = attempts.rename(columns={'id': 'attempt', 'time': 'attempt_time', 'status': 'attempt_status'})
            res = pd.merge(res, attempts, on='attempt')

            has_next = request['meta']['has_next']
            while has_next:
                # do pagination

                page += 1
                request = get_api_request(URL_FORMAT.format(step_id, page))

                if 'meta' not in request:
                    # if not success (e.g., error 404), then break
                    break

                new_res = pd.DataFrame(request['submissions'])
                attempts = pd.DataFrame(get_object('attempts', ids=new_res['attempt'].tolist()))
                attempts = attempts.rename(columns={'id': 'attempt', 'time': 'attempt_time', 'status': 'attempt_status'})
                new_res = pd.merge(new_res, attempts, on='attempt')

                res = res.append(new_res)
                has_next = request['meta']['has_next']

        res['step_id'] = step_id
        res['clue'] = ''

        if not submissions:
            submissions = res
        else:
            submissions = submissions.append(res)

    submissions['time'] = submissions['time'].apply(lambda x: int(datetime.datetime.strptime(x,
                                                    '%Y-%m-%dT%H:%M:%SZ').timestamp()))
    submissions['attempt_time'] = submissions['attempt_time'].apply(lambda x: int(datetime.datetime.strptime(x,
                                                    '%Y-%m-%dT%H:%M:%SZ').timestamp()))

    submissions = submissions.rename(columns={'id': 'submission_id',
                                              'attempt': 'attempt_id',
                                              'time': 'submission_time',
                                              'user': 'user_id'})

    submissions = submissions[header]
    submissions.to_csv(cached_name, index=False)

    return submissions


def get_featured_courses(cache=True):
    cached_name = 'cache/featured-courses.csv'

    if cache and os.path.isfile(cached_name):
        featured_courses = pd.read_csv(cached_name)
        return featured_courses

    URL_FORMAT = API_BASE_URL+'api/courses?is_featured=True&page={}'

    page = 1
    request = get_api_request(URL_FORMAT.format(page))
    if 'meta' not in request:
        # if not success (e.g., error 404), then return an empty list
        featured_courses = []
    else:
        # success
        featured_courses = pd.DataFrame(request['courses'])
        has_next = request['meta']['has_next']
        while has_next:
            # do pagination
            page += 1
            request = get_api_request(URL_FORMAT.format(page))

            if 'meta' not in request:
            # if not success (e.g., error 404), then break
                break

            new_res = pd.DataFrame(request['courses'])
            featured_courses = featured_courses.append(new_res)
            has_next = request['meta']['has_next']

    featured_courses = featured_courses.rename(columns={'id': 'course_id'})
    featured_courses = featured_courses.sort_values('course_id')

    featured_courses.to_csv(cached_name, index=False)

    return featured_courses







def print_featured_courses_report():
    URL_FORMAT = 'https://stepik.org/course-reports/{}'
    featured_courses = get_featured_courses()
    for course_id in featured_courses.course_id:
        print(URL_FORMAT.format(course_id))
