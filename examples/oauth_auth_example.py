# Run with Python 3
import requests

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
respDict = resp.json()
if (respDict.get('access_token',  "0") == "0"):
    print("can not auth with this id and secret")
    exit()

token = respDict['access_token']


# 3. Call API (https://stepic.org/api/docs/) using this token.
# Example:
api_url = 'https://stepic.org/api/courses/67'
course = requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).json()

print(course)
