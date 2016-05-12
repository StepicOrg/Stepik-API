# Run with Python 3
import json
import requests

# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = ...
client_secret = ...

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = json.loads(resp.text)['access_token']

# 3. Call API (https://stepic.org/api/docs/) using this token.
# Example:
api_url = 'https://stepic.org/api/courses/67'
course = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).text)

print(course)
