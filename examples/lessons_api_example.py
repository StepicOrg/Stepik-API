# Run with Python 3
import json
import requests
import pylab
import pandas as pd
import matplotlib.pyplot as plt

'''This example is made to be simple and useful. 
It demonstrates how to get lessons data via StepicAPI and why it can be useful.'''

# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = "put_yours_here"
client_secret = "put_yours_here"

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = json.loads(resp.text)['access_token']

# 3. Call API (https://stepic.org/api/docs/) using this token.
# Example:
api_url = 'https://stepic.org/api/lessons'
lessons = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).text)

lessons_data_frame = pd.DataFrame(lessons['lessons'])

passed = lessons_data_frame['passed_by'].values
time_to_complete = lessons_data_frame['time_to_complete'].values
viewed = lessons_data_frame['viewed_by'].values


# Drawing
plt.close('all')
f, (viewed_figure, passed_figure, difference_viwed_passed_figure) = plt.subplots(3, sharex=True, sharey=True)

viewed_figure.bar(time_to_complete, viewed)
viewed_figure.set_title('Comparison of viewed/passed')
viewed_figure.set_xlabel('time (s)')
viewed_figure.set_ylabel('Viewed this')

passed_figure.bar(time_to_complete, passed)
passed_figure.set_xlabel('time (s)')
passed_figure.set_ylabel('Passed this')

difference_viwed_passed_figure.bar(time_to_complete, viewed - passed)
difference_viwed_passed_figure.set_xlabel('time (s)')
difference_viwed_passed_figure.set_ylabel('Quited this')

f.subplots_adjust(hspace=0)

plt.savefig('quit.png')
