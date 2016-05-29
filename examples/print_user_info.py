# Run with Python 3
# Saves all step texts from course into single HTML file.

import json
import requests
from save_course_steps import fetch_object, fetch_objects

# Enter parameters below:
# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = "..."
client_secret = "..."
api_host = 'https://stepic.org'
user_id = 1

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = json.loads(resp.text)['access_token']

# 3. Call API (https://stepic.org/api/docs/) using this token.
user = fetch_object(api_host, 'user', user_id)

# 4. Print user info
print('Name: {} {}'.format(user['first_name'], user['last_name'])
print('Short bio: {}'.format(user['short_bio'])
print('Level: {}'.format(user['level'])
print('Knowledge: {}'.format(user['knowledge'])
print('Knowledge rank: {}'.format(user['knowledge_rank'])
print('Joined: {}'.format(user['join_date'])