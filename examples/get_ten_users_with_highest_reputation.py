
# coding: utf-8
import json
import requests
from operator import itemgetter

# Enter parameters below:
# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = ""
client_secret = ""

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = json.loads(resp.text)['access_token']

def get_users(tok):
    page = 1
    reputations = []
    logins = []
    api_url = 'https://stepic.org/api/users?page=' + str(page);
    result = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + tok}).text)
    while(result['meta']['has_next'] == True):
        page += 1
        profiles = result['users']
        for profile in profiles:
            reputations.append(profile['reputation'])
            name = profile['first_name'] + " " + profile['last_name']
            logins.append(name)
            api_url = 'https://stepic.org/api/users?page=' + str(page);
            result = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ tok}).text)
    return reputations, logins

indices, names = get_users(token)
users = [list(c) for c in zip(indices, names)]
users.sort(key=itemgetter(0), reverse=True)
for i in range(10):
    print(users[i])
