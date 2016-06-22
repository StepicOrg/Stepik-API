# Run with Python 3
import requests
import pandas as pd
import math
import copy

'''This example demonstrates how to get lessons data via Stepic-API and why it can be useful.'''

'''We download lessons' data one by one,
 then we make plots to see how much the loss of the people depends on the lesson time '''

plots_message = '<br /><hr>Plots describe how quantity of people who viewed, ' \
                'passed and left depends on lesson duration.'

enable_russian = '<head> <meta http-equiv="Content-Type" content="text/html; charset=utf-8" /> \n</head>'

welcome_message = 'Hi! <br><br>  Click on public lessons to check them out. ' \
                  '<br><hr> List of existing lessons with id from {} to {}: <br> '

setting_css_style = '<style> \nli { float:left; width: 49%; } \nbr { clear: left; } \n</style>'

start_lesson_id = 1
finish_lesson_id = 100

# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = "..."
client_secret = "..."


# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = resp.json()['access_token']


# Class for drawing plots in text
class Figure:
    def __init__(self, space_for_digits=10, rows=25, columns=120, bar_quantity_in_one_fifth_y=5,
                 underscore_quantity_in_one_fifth_x=20, divider_value=5, save_file='plot.html'):
        """
        :param space_for_digits: constant to make spare space for OY values
        :param rows: full quantity of bars (|) OY
        :param columns: full quantity of underscores (_) OX
        :param bar_quantity_in_one_fifth_y: how many bars (|) are in 1 of divider-value parts
        :param underscore_quantity_in_one_fifth_x: how many underscores (_) are in 1 of divider-value
        :param divider_value: how many parts axes are divided into
        :param save_file: html file where we save result
        """
        self.figure_matrix = []  # canvas
        self.rows = rows
        self.columns = columns
        self.space_for_digits = space_for_digits
        self.bar_quantity_y = bar_quantity_in_one_fifth_y
        self.underscore_quantity_x = underscore_quantity_in_one_fifth_x
        self.divider = divider_value
        self.file = save_file
        self.plot_matrix_list = []
        # creating empty canvas
        for r in range(self.rows):  # rows
            self.figure_matrix.append([])  # add empty
            for c in range(self.columns + self.space_for_digits):  # each column
                self.figure_matrix[r].append(' ')  # axes
        # drawing axes
        self.figure_matrix.append(['_'] * (self.columns + self.space_for_digits))
        self.figure_matrix.append([' '] * (self.columns + self.space_for_digits))
        for row in self.figure_matrix:
            row[self.space_for_digits] = '|'

    def add_barplot(self, x_axe, y_axe, name="Plot"):
        """
        adds new bar matrix to plot_matrix_list
        :param x_axe - list of values X to put on OX axe
        :param y_axe: - list of values Y to put on OY axe
        :param name - title of this plot
        """
        if x_axe and y_axe:
            # calculating canvas params of current plot
            max_x = max(x_axe)
            max_y = max(y_axe)
            step_y = max_y // self.divider
            step_x = max_x // self.divider
            value_of_bar = step_y / self.bar_quantity_y
            value_of_underscore = step_x / self.underscore_quantity_x
            current_plot_matrix = copy.deepcopy(self.figure_matrix)
            # drawing bars on figure_matrix canvas
            for point in range(len(x_axe)):
                current_x = x_axe[point]
                current_y = y_axe[point]
                if value_of_bar == 0:
                    y = max_y
                else:
                    y = round((max_y - current_y) // value_of_bar)
                if value_of_underscore == 0:
                    x = max_x
                else:
                    x = round(self.space_for_digits + current_x // value_of_underscore)
                for row_index in range(y, 26):
                    current_plot_matrix[row_index][x] = '*'
            i = 0
            # putting values on axe Y
            while max_y >= 0:
                for dig in range(len(str(max_y))):
                    current_plot_matrix[i][dig] = str(max_y)[dig]
                i += self.bar_quantity_y
                if max_y == step_y:
                    break
                max_y -= step_y
            # putting values on axe X
            i = self.space_for_digits
            x_value = 0
            while max_x >= x_value:
                for dig in range(len(str(x_value))):
                    current_plot_matrix[-1][i + dig] = str(x_value)[dig]
                i += self.underscore_quantity_x
                x_value += step_x
            # storing current plot in Figure field of all plots
            self.plot_matrix_list.append({"matrix": current_plot_matrix, "name": name})

    # saving plots given to html file
    def save_plots_to_html(self):
        f = open(self.file, 'a', encoding='utf-8')
        f.write('<big>{}</big>'.format(plots_message))
        for i in self.plot_matrix_list:
            f.write('<h2>{}</h2>\n<pre>'.format(i["name"]))
            for row in i["matrix"]:
                for symbol in row:
                    f.write(str(symbol))
                f.write('\n')
            f.write('\n\n')
            f.write('</pre><br>')


def introduce_lessons_in_html(start, finish, json_of_lessons, html_file='lessons.html'):
    """
    :param start: first id of lesson downloaded via API
    :param finish: last id of lesson downloaded via API
    :param json_of_lessons: json file we made by concatenating API answers that gave one-lesson-answer
    :param html_file: file we write to
    """
    with open(html_file, 'w', encoding='utf-8') as f:
        # enabling russian language and setting html style for two-columns lists
        f.write(enable_russian + setting_css_style)
        f.write('<big>{}</big><ol>\n'.format(welcome_message.format(start, finish)))
        for lesson in json_of_lessons:
            if lesson['is_public']:
                url = '<a href="https://stepic.org/lesson/{}">{}</a>'.format(lesson['slug'], lesson["title"])
                f.write('<li>{}</li>\n'.format(url))
            else:
                f.write('<li>{}</li> \n'.format(lesson['title']))
        f.write('</ol>\n')
        f.close()


# 3. Call API (https://stepic.org/api/docs/) using this token.
# Example:
def get_lessons_from_n_to_m(from_n, to_m, current_token):
    """
    :param from_n: starting lesson id
    :param to_m: finish lesson id
    :param current_token: token given by API
    :return: json object with all existing lessons with id from from_n to to_m
    """
    api_url = 'https://stepic.org/api/lessons/'
    json_of_n_lessons = []
    for n in range(from_n, to_m + 1):
        try:
            current_answer = (requests.get(api_url + str(n),
                                           headers={'Authorization': 'Bearer ' + current_token}).json())
            # check if lesson exists
            if not ("detail" in current_answer):
                json_of_n_lessons.append(current_answer['lessons'][0])
        except:
            print("Failure on id {}".format(n))
    return json_of_n_lessons


def nan_to_zero(*args):
    """
    :param args: lists with possible float-nan values
    :return: same list with all nans replaced by 0
    """
    for current_list in args:
        for i in range(len(current_list)):
            if not math.isnan(current_list[i]):
                current_list[i] = round(current_list[i])
            else:
                current_list[i] = 0


if __name__ == '__main__':
    # downloading lessons using API
    json_of_lessons_being_analyzed = get_lessons_from_n_to_m(start_lesson_id, finish_lesson_id, token)

    # storing the result in pandas DataFrame
    lessons_data_frame = pd.DataFrame(json_of_lessons_being_analyzed)

    # extracting the data needed
    passed = lessons_data_frame['passed_by'].values
    time_to_complete = lessons_data_frame['time_to_complete'].values
    viewed = lessons_data_frame['viewed_by'].values
    left = viewed - passed

    # replacing data-slices by lists of their values
    time_to_complete = time_to_complete.tolist()
    viewed = viewed.tolist()
    passed = passed.tolist()
    left = left.tolist()

    # replacing nan-values with 0 and rounding values
    nan_to_zero(time_to_complete, viewed, passed, left)

    # creating new Figure to make plots
    figure1 = Figure(save_file='lessons.html')

    # adding bar diagrams to Figure f1
    figure1.add_barplot(time_to_complete, viewed, "X -- time to complete | Y - quantity of people who viewed")
    figure1.add_barplot(time_to_complete, passed, "X -- time to complete | Y - quantity of people who passed")
    figure1.add_barplot(time_to_complete, left, "X -- time to complete | Y - quantity of people who left")

    # creating html-file describing lessons
    introduce_lessons_in_html(start_lesson_id, finish_lesson_id, json_of_lessons_being_analyzed, 'lessons.html')
    # saving plots (file is linked with Figure object f1)
    figure1.save_plots_to_html()
