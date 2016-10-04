import argparse
import shutil
import os

import matplotlib.pyplot as plt
import pandas as pd

from library.api import API_HOST, get_token, fetch_objects
from library.settings import ITEM_FORMAT, OPTION_FORMAT, STEP_FORMAT
from library.utils import (html2latex, create_answer_matrix, get_course_structure,
                           get_course_submissions, get_step_options,
                           get_item_statistics, get_question, process_step_url, process_options_with_name,
                           get_video_peaks, get_video_stats)


class ExternalCourseReport:
    default_project_folder = 'default'
    default_report_name = 'course-report'
    course_project_folder = 'course-{}'
    course_report_name = 'course-{}-report'

    def __init__(self):
        self.course_id = 0

    def get_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--course', type=int, help='course id')
        parser.add_argument('-n', '--nocache', action='store_true', help='no cache when generate latex report')
        parser.add_argument('-u', '--update', action='store_true', help='update project when compile latex report')
        return parser

    def build(self):
        args = self.get_parser().parse_args()

        if args.course:
            self.course_id = args.course
            cached = not bool(args.nocache)
            update = bool(args.update)

            print('Course {} processing...'.format(self.course_id))

            base = 'latex/'
            directory_name = self.course_project_folder.format(self.course_id)
            full_directory = base + directory_name

            if not os.path.exists(full_directory):
                shutil.copytree(base + self.default_project_folder, full_directory)

            self.generate_latex_report(full_directory + '/generated/', cached=cached)
            self.compile_latex_report(full_directory, update=update)

    def generate_latex_report(self, directory, cached=True):
        pass

    def compile_latex_report(self, directory, update=True):
        latex_command = 'pdflatex -synctex=1 -interaction=nonstopmode {}.tex'.format(self.default_report_name)

        os.chdir(directory)

        if update:
            os.system('cp -rf ../{}/* .'.format(self.default_project_folder))

        # Launch LaTeX three times
        os.system(latex_command)
        os.system(latex_command)
        os.system(latex_command)

        report_name = self.course_report_name.format(self.course_id)
        os.system('cp {}.pdf ../../pdf/{}.pdf'.format(self.default_report_name, report_name))


class ItemReport(ExternalCourseReport):
    default_project_folder = 'default-item'
    default_report_name = 'course-item-report'
    course_project_folder = 'course-{}-item'
    course_report_name = 'course-{}-item-report'

    def generate_latex_report(self, directory, cached=True):
        course_id = self.course_id
        course_info = fetch_objects('courses', pk=course_id)
        course_title = course_info[0]['title']
        course_url = '{}/course/{}'.format(API_HOST, course_id)
        with open('{}info.tex'.format(directory), 'w') as info_file:
            info_file.write('\\def\\coursetitle{{{}}}\n\\def\\courseurl{{{}}}\n'.format(course_title, course_url))

        course_structure_filename = 'cache/course-{}-structure.csv'.format(course_id)
        if os.path.isfile(course_structure_filename) and cached:
            course_structure = pd.read_csv(course_structure_filename)
        else:
            course_structure = get_course_structure(course_id)
            course_structure.to_csv(course_structure_filename, index=False)

        # course_structure = course_structure[course_structure.step_type == 'choice']
        # course_structure.drop(['begin_date', 'hard_deadline'], axis=1, inplace=True)
        course_structure['step_variation'] = course_structure.groupby(['lesson_id', 'step_position']).cumcount()
        course_structure['step_variation'] += 1

        submissions_filename = 'cache/course-{}-submissions.csv'.format(course_id)
        if os.path.isfile(submissions_filename) and cached:
            submissions = pd.read_csv(submissions_filename)
        else:
            submissions = get_course_submissions(course_id, course_structure)
            submissions.to_csv(submissions_filename, index=False)

        submissions = pd.merge(submissions, course_structure, on='step_id')

        item_statistics = self.perform_item_analysis(submissions, course_structure, cached)
        option_statistics = self.perform_option_analysis(submissions, cached)
        self.generate_latex_files(item_statistics, option_statistics, directory)

    def perform_item_analysis(self, submissions, course_structure, cached=True):
        # item statistics
        course_id = self.course_id
        item_statistics_filename = 'cache/course-{}-item-statistics.csv'.format(course_id)
        if os.path.isfile(item_statistics_filename) and cached:
            item_statistics = pd.read_csv(item_statistics_filename)
        else:
            answers = create_answer_matrix(submissions, 'user_id', 'step_id', 'status',
                                           lambda x: int('wrong' not in x.tolist()), 'submission_time')

            item_statistics = get_item_statistics(answers)
            if item_statistics.empty:
                return

            item_statistics = item_statistics.rename(columns={'item': 'step_id'})
            item_statistics = pd.merge(item_statistics, course_structure, on='step_id')

            item_statistics['step_url'] = item_statistics.apply(process_step_url, axis=1)
            item_statistics['question'] = item_statistics['step_id'].apply(get_question)

            item_statistics = item_statistics.sort_values(['module_position', 'lesson_position',
                                                           'step_position', 'step_id'])
            item_statistics.to_csv(item_statistics_filename, index=False)
        return item_statistics

    def perform_option_analysis(self, submissions, cached=True, with_distractors=False):
        course_id = self.course_id
        option_statistics_filename = 'cache/course-{}-option-statistics.csv'.format(course_id)
        if os.path.isfile(option_statistics_filename) and cached:
            option_statistics = pd.read_csv(option_statistics_filename)
        else:
            if with_distractors:
                option_statistics = pd.DataFrame(columns=['step_id', 'is_multiple',
                                                          'is_correct', 'option_id', 'option_name',
                                                          'clue', 'difficulty', 'discrimination'])
            else:
                option_statistics = pd.DataFrame(columns=['step_id', 'is_multiple',
                                                          'is_correct', 'option_id', 'option_name'])
            option_statistics[['step_id', 'option_id']] = option_statistics[['step_id', 'option_id']].astype(int)
            for step_id in submissions.step_id.unique():
                step_submissions = submissions[submissions.step_id == step_id]
                if step_submissions.empty:
                    continue
                if step_submissions.step_type.tolist()[0] != 'choice':
                    continue

                print('Option analysis for step_id = ', step_id)
                option_names = get_step_options(step_id)

                if with_distractors:
                    step_options = pd.DataFrame(columns=['user_id', 'is_multiple', 'option_id', 'answer', 'clue'])
                    for _, row in step_submissions.iterrows():
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
                    step_statistics[['is_correct']] = step_statistics[['clue']]
                else:
                    step_statistics = option_names
                option_statistics = option_statistics.append(step_statistics)

            option_statistics.to_csv('cache/course-{}-option-statistics.csv'.format(course_id), index=False)
        return option_statistics

    def generate_latex_files(self, item_statistics, option_statistics, directory):
        # TODO: Improve recommendations based on item and option statistics
        def get_recommendation(item, options):
            recommendation = ''
            difficulty = item.difficulty
            discrimination = item.discrimination
            item_total_corr = item.item_total_corr

            if options.empty or ('difficulty' not in options.columns.values):
                n_nonfunct_options = 0
            else:
                nonfunct_options = options[(options.difficulty < 0.05) & ~(options.is_correct)]
                n_nonfunct_options = nonfunct_options.shape[0]

            if difficulty < 0.05:
                recommendation += 'Задание слишком легкое, его лучше пересмотреть или удалить.\n\n'
            elif difficulty > 0.95:
                recommendation += 'Задание слишком сложное: проверьте, правильно ли оно составлено.\n\n'

            if (discrimination <= 0) or (item_total_corr <= 0):
                recommendation += 'У задания отрицательная дискриминативность: ' + \
                                  'если оно корректно составлено, то его лучше исключить.\n\n'

            if (0 < discrimination) and (discrimination < 0.3):
                recommendation += 'У задания низкая дискриминативность: его можно оставить в качесте тренировочного задания, ' + \
                                  'но для проверки знаний его лучше не использовать.\n\n'

            if (0 < item_total_corr) and (item_total_corr < 0.2):
                recommendation += 'Данное задание слабо коррелирует с суммарным баллом: ' + \
                                  'возможно, оно проверяет не то же самое, что проверяют другие задания.\n\n'

            if n_nonfunct_options:
                recommendation += 'Данное задание содержит нефункциональные опции: их нужно заменить или удалить.\n\n'
            return recommendation

        with open('{}map.tex'.format(directory), 'w') as map_file:
            map_file.write('')

        for ind, item in item_statistics.iterrows():
            with open('{}map.tex'.format(directory), 'a') as map_file:
                map_file.write('\\input{{generated/step-{}.tex}}\n'.format(item.step_id))
            with open('{}step-{}.tex'.format(directory, item.step_id), 'w') as item_file:
                item_file.write(ITEM_FORMAT.format(item=item))

                if item.step_type != 'choice':
                    continue

                has_difficulty = bool('difficulty' in option_statistics.columns.values)
                if has_difficulty:
                    item_file.write('\n\n\\begin{options}\n')
                item_option_statistics = option_statistics[option_statistics.step_id == item.step_id]

                for op_ind, option in item_option_statistics.iterrows():
                    label = ''
                    if option.is_multiple:
                        label += '\multiple'
                    else:
                        label += '\single'
                    if option.is_correct:
                        label += 'correct'
                    else:
                        label += 'wrong'

                    option.option_name = html2latex(option.option_name)
                    if not has_difficulty:
                        difficulty = ''
                    else:
                        difficulty = '{:.2f}'.format(option.difficulty)

                    item_file.write(OPTION_FORMAT.format(label=label, name=option.option_name,
                                                         difficulty=difficulty))

                if has_difficulty:
                    item_file.write('\\end{options}\n\n')

                item_recommendation = get_recommendation(item, item_option_statistics)

                if item_recommendation:
                    item_file.write('\\begin{recommendations}\n')
                    item_file.write(item_recommendation)
                    item_file.write('\\end{recommendations}\n')
                else:
                    item_file.write('%\\begin{recommendations}\n\n%\\end{recommendations}\n')


class VideoReport(ExternalCourseReport):
    default_project_folder = 'default-video'
    default_report_name = 'course-video-report'
    course_project_folder = 'course-{}-video'
    course_report_name = 'course-{}-video-report'

    def generate_latex_report(self, directory, cached=True):
        course_id = self.course_id
        token = get_token()

        course_structure = get_course_structure(course_id)
        course_structure = course_structure.loc[course_structure.step_type == 'video',
                                                ['step_id', 'step_position', 'lesson_id']]

        course_info = fetch_objects('courses', pk=course_id)
        course_title = course_info[0]['title']
        course_url = '{}/course/{}'.format(API_HOST, course_id)

        with open('{}info.tex'.format(directory), 'w') as info_file:
            info_file.write('\\def\\coursetitle{{{}}}\n\\def\\courseurl{{{}}}\n'.format(course_title, course_url))

        with open('{}map.tex'.format(directory), 'w') as map_file:
            map_file.write('')

        total_peaks = pd.DataFrame()
        for ind, row in course_structure.iterrows():
            step_id = row.step_id
            step_url = 'https://stepik.org/lesson/{}/step/{}'.format(row.lesson_id, row.step_position)

            stats = get_video_stats(step_id, cached, token)

            fig = plt.figure()
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)
            windows = get_video_peaks(stats, plot=True, ax=ax1, ax2=ax2)

            windows['step_id'] = step_id
            windows['course_id'] = course_id
            windows['step_url'] = step_url

            windows['start_sec'] = windows['start'].apply(lambda x: '{:02d}:{:02d}'.format(x//60, x%60))
            windows['end_sec'] = windows['end'].apply(lambda x: '{:02d}:{:02d}'.format(x//60, x%60))

            self.generate_latex_files(course_id, step_id, step_url, windows, directory)
            fig.savefig('{}step_{}.png'.format(directory, step_id))
            plt.close()

            if total_peaks.empty:
                total_peaks = windows
            else:
                total_peaks = total_peaks.append(windows)

        total_peaks.to_csv('cache/course-{}-totalpeaks.csv'.format(course_id), index=False)

        # total_peaks = pd.read_csv('cache/course-{}-totalpeaks.csv'.format(course_id))
        total_peaks = total_peaks.sort_values('area',  ascending=False)
        if total_peaks.shape[0] <= 5:
            top_peaks = total_peaks
        else:
            top_peaks = total_peaks[0:5]

        with open('{}total.tex'.format(directory), 'w') as total_file:
            if not total_peaks.empty:
                total_file.write('В курсе выделены следующие пики, имеющие максимальную относительную площадь.\n')
                total_file.write('Проверьте, нет ли в данных местах у учащихся ' +
                                 'трудностей с пониманием учебного материала.\n')

                total_file.write('\\begin{totalpeaks}\n')
                for ind, row in top_peaks.iterrows():
                    total_file.write('\\totalpeak{{{}}}{{{}}}{{{}}}{{{}}}{{{:.2f}}}\n'.format(row.step_id,
                                                                                        row.step_url,
                                                                                        row.start_sec,
                                                                                        row.end_sec,
                                                                                        row.area))
                total_file.write('\\end{totalpeaks}\n')
            else:
                total_file.write('\n')

    def generate_latex_files(self, course_id, step_id, step_url, windows, directory):

        with open('{}map.tex'.format(directory), 'a') as map_file:
            map_file.write('\\input{{generated/step_{}.tex}}\n'.format(step_id))

        with open('{}step_{}.tex'.format(directory, step_id), 'w') as step_file:
            step_file.write(STEP_FORMAT.format(step_id=step_id, step_url=step_url))

            if windows.empty:
                step_file.write('\n\nПики не обнаружены.\n')
            else:
                step_file.write('\n\n\\begin{peaks}\n')
                for ind, row in windows.iterrows():
                    step_file.write('\peak{{{}}}{{{}}}{{{:.2f}}}{{{:.2f}}}{{{:.2f}}}\n'.format(row.start_sec,
                                                                                               row.end_sec,
                                                                                               row.width,
                                                                                               row.height,
                                                                                               row.area))
                step_file.write('\\end{peaks}\n\n')

