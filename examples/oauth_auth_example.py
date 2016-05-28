# Run with Python 3
import json
import requests

# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id ="gtz2Zo4Itm1CDqSRHmLSIaA4dKCukiTwWgcs1VB6"
client_secret =" vnbKuO0oAfW1iUFSwsHJshj2gtOEFRZtpo60bg7oDW9XM0WyGJJH2uvHXNgHjTYWsfsE38J8t2F2s3JAHgag17nkRj8EVM51IqoLQAwCdYcGcATeRJp1rDV43EsbkHX9"

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )

respDict = json.loads(resp.text);
if (respDict.get('access_token', None) == None):
    print("can not auth with this id and secret")
    exit()

token = respDict['access_token']

# 3. Call API (https://stepic.org/api/docs/) using this token.
# Example:

api_url = 'https://stepic.org/api/cource/67'
course = json.loads(requests.get(api_url, headers={"Authorization": "Bearer"+ token}).text)

#print(course)
