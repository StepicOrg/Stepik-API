import ast
import csv
import datetime
import time

import numpy as np
import pandas as pd
import pypandoc

from api import API_HOST, fetch_objects, fetch_objects_by_id, get_token


def get_unix_date(date):
    timestamp = time.mktime(datetime.datetime.strptime(date.split('+')[0], "%Y-%m-%dT%H:%M:%SZ").timetuple())
    return timestamp


def html2latex(text):
    output = pypandoc.convert(text, 'latex', format='html', extra_args=['-f', 'html+tex_math_dollars'])
    return output


def process_step_url(row):
    if ('max_step_variation' not in row.index) or (row.max_step_variation == 1):
        # no step variations
        return '{}/lesson/{}/step/{}'.format(API_HOST, row.lesson_id, row.step_position)
    return '{}/lesson/{}/step/{}?alternative={}'.format(API_HOST,
                                                        row.lesson_id, row.step_position, row.step_variation)


# API functions

def get_course_structure(course_id, token=None):
    if not token:
        token = get_token()
    course = fetch_objects_by_id('courses', course_id, token=token)[0]
    sections = fetch_objects('sections', token=token, id=course['sections'])

    unit_ids = [unit for section in sections for unit in section['units']]
    units = fetch_objects('units', token=token, id=unit_ids)

    lesson_ids = [unit['lesson'] for unit in units]
    lessons = fetch_objects('lessons', token=token, id=lesson_ids)

    step_ids = [step for lesson in lessons for step in lesson['steps']]
    steps = fetch_objects('steps', token=token, id=step_ids)
    step_id = [step['id'] for step in steps]
    step_position = [step['position'] for step in steps]
    step_type = [step['block']['name'] for step in steps]
    step_lesson = [step['lesson'] for step in steps]
    step_correct_ratio = [step['correct_ratio'] for step in steps]

    course_structure = pd.DataFrame({'course_id': course_id,
                                     'lesson_id': step_lesson,
                                     'step_id': step_id,
                                     'step_position': step_position,
                                     'step_type': step_type,
                                     'step_correct_ratio': step_correct_ratio})

    module_position = [[section['position']]*len(section['units']) for section in sections]
    module_position = [value for small_list in module_position for value in small_list]

    module_id = [[section['id']]*len(section['units']) for section in sections]
    module_id = [value for small_list in module_id for value in small_list]

    module_hard_deadline = [[section['hard_deadline']]*len(section['units']) for section in sections]
    module_hard_deadline = [value for small_list in module_hard_deadline for value in small_list]

    module_begin_date = [[section['begin_date']]*len(section['units']) for section in sections]
    module_begin_date = [value for small_list in module_begin_date for value in small_list]

    lesson_position = [unit['position'] for unit in units]

    module_structure = pd.DataFrame({'lesson_id': lesson_ids,
                                     'lesson_position': lesson_position,
                                     'module_id': module_id,
                                     'module_position': module_position,
                                     'hard_deadline': module_hard_deadline,
                                     'begin_date': module_begin_date})

    course_structure = course_structure.merge(module_structure)
    course_structure = course_structure.sort_values(['module_position', 'lesson_position', 'step_position'])
    return course_structure


def get_course_submissions(course_id, course_structure=pd.DataFrame(), token=None):
    header = ['submission_id', 'user_id', 'step_id', 'attempt_id', 'status', 'submission_time', 'reply', 'hint']
    if not token:
        token=get_token()

    if course_structure.empty:
        course_structure = get_course_structure(course_id, token)

    course_submissions = pd.DataFrame()
    for step in course_structure.step_id.unique().tolist():
        step_submissions = pd.DataFrame(fetch_objects('submissions', token=token, step=step))
        if step_submissions.empty:
            continue

        step_submissions = step_submissions.rename(columns={'id': 'submission_id',
                                                            'time': 'submission_time',
                                                            'attempt': 'attempt_id'})
        attempt_ids = step_submissions['attempt_id'].unique().tolist()
        step_attempts = pd.DataFrame(fetch_objects_by_id('attempts', attempt_ids, token=token))
        step_attempts = step_attempts.rename(columns={'id': 'attempt_id',
                                                      'time': 'attempt_time',
                                                      'status': 'attempt_status'})
        step_submissions = pd.merge(step_submissions, step_attempts, on='attempt_id')
        step_submissions['step_id'] = step
        course_submissions = course_submissions.append(step_submissions)

    if course_submissions.empty:
        return pd.DataFrame(columns=header)

    course_submissions['submission_time'] = course_submissions['submission_time'].apply(get_unix_date)
    course_submissions['attempt_time'] = course_submissions['attempt_time'].apply(get_unix_date)

    course_submissions = course_submissions.rename(columns={'user': 'user_id'})
    course_submissions = course_submissions[header]
    return course_submissions


def get_enrolled_users(course_id, token=None):
    if not token:
        token = get_token()

    learner_group = fetch_objects('courses', token=token, pk=course_id)[0]['learners_group']
    users = fetch_objects('groups', token=token, pk=learner_group)[0]['users']

    return users


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


def get_question(step_id):
    source = fetch_objects('step-sources', id=step_id)

    try:
        question = source[0]['block']['text']
    except:
        question = '\n'

    question = html2latex(question)

    return question


def get_step_options(step_id):
    source = fetch_objects('step-sources', id=step_id)

    try:
        options = source[0]['block']['source']['options']
        options = pd.DataFrame(options)
        is_multiple = source[0]['block']['source']['is_multiple_choice']
    except KeyError:
        options = pd.DataFrame(columns=['step_id', 'option_id', 'option_name', 'is_correct', 'is_multiple'])
        return options

    options['step_id'] = step_id
    options['is_multiple'] = is_multiple
    options = options.sort_values('text').reset_index()
    options = options.rename(columns={'text': 'option_name'})
    options['option_id'] = options.index + 1
    options = options[['step_id', 'option_id', 'option_name', 'is_correct', 'is_multiple']]

    return options


# IRT functions

def create_answer_matrix(data, user_column, item_column, value_column, aggfunc=np.mean, time_column=None):
    if time_column:
        # select only the first response
        data = data.loc[data.groupby([item_column, user_column])[time_column].idxmin()]
        data = data.drop_duplicates(subset=[item_column, user_column])

    answers = pd.pivot_table(data, values=[value_column], index=[user_column], columns=[item_column],
                             aggfunc=aggfunc)

    if not answers.empty:
        answers = answers[value_column]

    return answers


# TODO: add Cronbach's alpha to item statistics
# see http://stackoverflow.com/questions/20799403/improving-performance-of-cronbach-alpha-code-python-numpy
def get_item_statistics(answers, discrimination_prop=0.3):
    total_people = answers.shape[0]

    n_people = answers.count(axis=0)

    # use mean (not sum) because of NA values
    item_difficulty = 1 - answers.mean(axis=0)
    total_score = answers.mean(axis=1)
    item_total_corr = answers.corrwith(total_score)

    n_top_people = int(discrimination_prop * total_people)
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
