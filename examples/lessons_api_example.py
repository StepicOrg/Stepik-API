# Run with Python 3
import requests
import pandas as pd
import math


class figure():
    def __init__(self, space_for_digits=10, rows=25, columns=120, bar_quantity_y=5, underscore_quantity_x=20,
                 divider=5):
        self.figure_matrix = []
        self.rows = rows
        self.columns = columns
        self.space_for_digits = space_for_digits
        self.bar_quantity_y = bar_quantity_y
        self.underscore_quantity_x = underscore_quantity_x
        self.divider = divider
        for r in range(self.rows):  # rows
            self.figure_matrix.append([])  # add empty
            for c in range(self.columns + self.space_for_digits):  # each column
                self.figure_matrix[r].append(' ')
                # axes
        self.figure_matrix.append(['_'] * (self.columns + self.space_for_digits))
        self.figure_matrix.append([' '] * (self.columns + self.space_for_digits))
        for row in self.figure_matrix: row[self.space_for_digits] = '|'

    def barplot(self, x_axe, y_axe, name="Plot"):
        if x_axe and y_axe:
            max_x = max(x_axe)
            max_y = max(y_axe)
            step_y = max_y // self.divider
            step_x = max_x // self.divider
            value_of_bar = step_y / self.bar_quantity_y
            value_of_unredscore = step_x / self.underscore_quantity_x

            for point in range(len(x_axe)):
                current_x = x_axe[point]
                current_y = y_axe[point]
                y = round((max_y - current_y) // value_of_bar)
                x = round(self.space_for_digits + current_x // value_of_unredscore)
                for i in range(y, 26):
                    self.figure_matrix[i][x] = '*'
            i = 0
            while max_y >= 0:
                for dig in range(len(str(max_y))):
                    self.figure_matrix[i][dig] = str(max_y)[dig]
                i += self.bar_quantity_y
                max_y -= step_y

            i = self.space_for_digits
            x_value = 0
            while max_x >= x_value:
                for dig in range(len(str(x_value))):
                    self.figure_matrix[-1][i + dig] = str(x_value)[dig]
                i += self.underscore_quantity_x
                x_value += step_x

            f = open('plot.txt', 'a')
            f.write(str(name) + '\n')
            for row in self.figure_matrix:
                for symb in row:
                    f.write(str(symb))
                f.write('\n')
            f.write('\n\n')


'''This example is made to be simple and useful.
It demonstrates how to get lessons data via StepicAPI and why it can be useful.'''

# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = "put_urs"
client_secret = "put_urs"

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )

token = resp.json()['access_token']

# 3. Call API (https://stepic.org/api/docs/) using this token.
# Example:
api_url = 'https://stepic.org/api/lessons'
lessons = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).json()

lessons_data_frame = pd.DataFrame(lessons['lessons'])

passed = lessons_data_frame['passed_by'].values
time_to_complete = lessons_data_frame['time_to_complete'].values
viewed = lessons_data_frame['viewed_by'].values
left = viewed - passed

time_to_complete = time_to_complete.tolist()
viewed = viewed.tolist()
passed = passed.tolist()
left = left.tolist()

for i in range(len(time_to_complete)):
    if not math.isnan(time_to_complete[i]):
        time_to_complete[i] = round(time_to_complete[i])
    else:
        time_to_complete[i] = 0

f = open('plot.txt', 'w')

f1 = figure()
f1.barplot(time_to_complete, viewed, "Viewed/Duration of lesson")
f2 = figure()
f2.barplot(time_to_complete, passed, "Passed/Duration of lesson")
f3 = figure()
f3.barplot(time_to_complete, left, "Left/Duration of lesson")
