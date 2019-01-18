# Run with Python 3
import requests
from random import randint
from os.path import splitext
import math
import json


# 1. Get your keys at https://stepik.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = "..."
client_secret = "..."

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepik.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = resp.json()['access_token']

# 3. Call API (https://stepik.org/api/docs/) using this token.


# Get leaders by count
def get_leaders(count):
    pages = math.ceil(count / 20)
    leaders = []
    for page in range(1, pages + 1):
        api_url = 'https://stepik.org/api/users?order=knowledge_rank&page={}'.format(page)
        response = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).text)
        leaders += response['users']
        if not response['meta']['has_next']:
            break

    return leaders


# Get leader user randomly from 100 leaders and download his avatar
avatar_url = get_leaders(100)[randint(0, 99)]['avatar']
response = requests.get(avatar_url, stream=True)
extension = splitext(avatar_url)[1]

with open('leader{}'.format(extension), 'wb') as out_file:
    out_file.write(response.content)
