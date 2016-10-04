import ast
import datetime
import time
import math
import pypandoc
import os

import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import pandas as pd
import statsmodels.api as sm

from library.api import API_HOST, fetch_objects, fetch_objects_by_id, get_token
from library.settings import MIN_VIDEO_LENGTH


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


# Video report

def get_video_stats(step_id, cached=True, token=None):
    if not token:
        token = get_token()

    cached_name = 'cache/step-{}-videostats.csv'.format(step_id)

    if cached and os.path.isfile(cached_name):
        stats = pd.read_csv(cached_name)
        return stats

    stats = pd.DataFrame(fetch_objects('video-stats', token=token, step=step_id))

    if not stats.empty:
        stats.to_csv(cached_name, index=False)
        stats = pd.read_csv(cached_name)
    return stats


def get_video_peaks(stats, plot=False, ax=None, ax2=None):
    header = ['start', 'peak', 'end', 'rise_rate', 'is_common',
              'width', 'height', 'area']

    if stats.empty:
        return pd.DataFrame(columns=header)
    row = stats.loc[stats.index[0]]

    try:
        watched_first = np.array(ast.literal_eval(row['watched_first']))
        watched_total = np.array(ast.literal_eval(row['watched_total']))
        play = np.array(ast.literal_eval(row['play']))
    except ValueError:
        return pd.DataFrame(columns=header)

    # use only shortest data for analyses
    video_length = min(len(watched_first), len(watched_total), len(play))
    if video_length < MIN_VIDEO_LENGTH:
        return pd.DataFrame(columns=header)

    watched_first = watched_first[:video_length]
    watched_total = watched_total[:video_length]
    play = play[:video_length]

    play[0] = play[1]  # ignore auto-play in the beginning

    rewatching = watched_total - watched_first

    # To fight the noise, use smoothing technique before analysis
    rewatching = get_smoothing_data(rewatching, frac=0.05)
    play = get_smoothing_data(play, frac=0.1)

    rewatch_windows = detect_peaks(rewatching)
    play_windows = detect_peaks(play)

    rewatch_windows['is_common'] = False
    play_windows['is_common'] = False

    # find common windows
    for ind, row in rewatch_windows.iterrows():
        start = row['start']
        end = row['end']
        if play_windows.loc[~((play_windows.end < start) | (end < play_windows.start))].shape[0] > 0:
            rewatch_windows.loc[ind, 'is_common'] = True

    common_windows = rewatch_windows[rewatch_windows.is_common].copy()

    if plot:
        peak_plot(rewatching, rewatch_windows, ax)
        if ax:
            ax.set_ylabel('Num rewatchers', fontsize=10)
        peak_plot(play, play_windows, ax2)
        if ax2:
            ax2.set_xlabel('Time in video (seconds)', fontsize=10)
            ax2.set_ylabel('Num play events', fontsize=10)

    # calculate peak features (normalized width, height, and area)
    total_length = len(rewatching)
    total_height = max(rewatching)
    total_area = sum(rewatching)

    if not common_windows.empty:
        common_windows['width'] = common_windows.apply(lambda x: (x['end']-x['start'])/total_length, axis=1)
        common_windows['height'] = common_windows.apply(lambda x: rewatching[x['peak']]/total_height, axis=1)
        common_windows['area'] = common_windows.apply(
            lambda x: rewatching[x['start']:x['end']].sum()/total_area, axis=1)
    else:
        common_windows = pd.DataFrame(columns=header)

    return common_windows



def get_smoothing_data(data, frac=0.05):
    """
    Return smoothing data based on LOWESS (Locally Weighted Scatterplot Smoothing)
    :param data: 1-D numpy array of values
    :param frac: Between 0 and 1. The fraction of the data used when estimating each value
    :return: 1-D numpy array of smoothing values
    """
    smoothing_data = sm.nonparametric.lowess(data, np.arange(len(data)), frac=frac, return_sorted=False)
    return smoothing_data


# TwitInfo Peak Detection Algorithm
# Paper:
# http://hci.stanford.edu/publications/2011/twitinfo/twitinfo-chi2011.pdf
# Code source:
# https://github.com/pmitros/LectureScapeBlock/blob/ac16ec00dc018e5b17a8c23a025f98e693695527/lecturescape/lecturescape/algorithms.py
# updated for peaks finding
def detect_peaks(data, tau=1.5):
    """
    peak detection algorithm
    """

    def detect_peaks_update(old_mean, old_mean_dev, update_value):
        ALPHA = 0.125
        diff = math.fabs(old_mean - update_value)
        new_mean_dev = ALPHA * diff + (1-ALPHA) * old_mean_dev
        new_mean = ALPHA * update_value + (1-ALPHA) * old_mean
        return [new_mean, new_mean_dev]

    bins = data
    P = 5
    TAU = tau

    # list of peaks - their start, end, and peak time
    windows = pd.DataFrame(columns=['start', 'peak', 'end', 'rise_rate'])
    if len(bins) <= 5:
        return windows

    if np.isnan(bins[5]) or bins[5] is ma.masked or bins[5] == 0:
        mean = np.mean(bins)
    else:
        mean = bins[5]
    if np.isnan(np.var(bins[5:5+P])) or np.var(bins[5:5+P]) is ma.masked or np.var(bins[5:5+P]) == 0:
        meandev = np.var(bins)
    else:
        meandev = np.var(bins[5:5+P])

    i = 5
    while i < len(bins):
        if np.isnan(bins[i]) or bins[i] is ma.masked:
            i += 1
            continue
        rise_rate = math.fabs(bins[i] - mean) / meandev
        if rise_rate > TAU and bins[i] > bins[i-1]:
            start = i - 1
            while i < len(bins) and bins[i] > bins[i-1]:
                [mean, meandev] = detect_peaks_update(mean, meandev, bins[i])
                i += 1
            peak = i - 1
            end = i

            # until the bin counts are back at the level they started
            while i < len(bins) and bins[i] > bins[start]:
                # UPDATE: the peak point should be maximum between start and end
                if bins[peak] < bins[i-1] and bins[i] < bins[i-1]:
                    peak = i - 1

                if math.fabs(bins[i] - mean) / meandev > TAU and bins[i] > bins[i-1]:
                    # another significant rise found, so going back and quit the downhill climbing
                    while bins[i] > bins[i-1] and i > start:
                        i -= 1
                    end = i
                    break

                [mean, meandev] = detect_peaks_update(mean, meandev, bins[i])
                i += 1
                end = i

            windows = windows.append({'start': start,
                            'peak': peak,
                            'end': end,
                            'rise_rate': rise_rate}, ignore_index=True)
        else:
            [mean, meandev] = detect_peaks_update(mean, meandev, bins[i])
        i += 1

    windows[['start', 'peak', 'end']] = windows[['start', 'peak', 'end']].astype(int)
    #print(windows)

    return windows


def peak_plot(data, windows, ax):
    """Plot results of the detect_peaks function."""

    peak_index = np.array(windows['peak'].tolist())

    if not ax:
        _, ax = plt.subplots(1, 1, figsize=(8, 4))

    ax.plot(data, '#66CC66', lw=1)

    if peak_index.size:
        #label = 'peak'
        #label = label + 's' if peak_index.size > 1 else label
        #ax.plot(peak_index, data[peak_index], '+', mfc=None, mec='r', mew=2, ms=8,
        #        label='%d %s' % (peak_index.size, label))

        for ind, row in windows.iterrows():
            start = row['start']
            end = row['end']
            is_common = row['is_common']
            width = end - start

            if is_common:
                fill_color = '#A5E5A5'
            else:
                fill_color = '#CCCCCC'
            ax.fill_between(np.arange(start, end), np.zeros(width), data[start:end],
                            interpolate=True, facecolor=fill_color, linewidth=0.0)

        ax.legend(loc='best', framealpha=.5, numpoints=1)

    ax.set_xlim(-.02*data.size, data.size*1.02-1)
    ymin, ymax = data[np.isfinite(data)].min(), data[np.isfinite(data)].max()
    yrange = ymax - ymin if ymax > ymin else 1
    ax.set_ylim(0, ymax + 0.1*yrange)
