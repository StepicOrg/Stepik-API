# coding: utf-8
import json
import requests
from operator import itemgetter

# Enter parameters below:
# 1. Get your keys at https://stepik.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = "..."
client_secret = "..."

class Getter(object):
    def __init__(self, client_id, secret_id):
        self.client_id = client_id
        self.secret_id = secret_id
        self.url = 'https://stepik.org/api/'
        try:
            auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
            resp = requests.post('https://stepik.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth
                         ).json()
            self.token = resp['access_token']
        except:
            print("Unable to get token")

    def get(self, url):
        try:
            resp = requests.get(url, headers={'Authorization': 'Bearer ' + self.token}).json()
        except:
            print("Unable to get data")
            resp = None
        return resp


    def get_users(self):
        page = 0
        reputations = []
        logins = []
        has_next = True
        while(has_next):
            page += 1
            cur_url = ("{}/users?page={}").format(self.url, page);
            result = self.get(cur_url)
            profiles = result['users']
            has_next = result['meta']['has_next']
            for profile in profiles:
                reputations.append(profile['reputation'])
                name = profile['first_name'] + " " + profile['last_name']
                logins.append(name)
        users = [list(c) for c in zip(reputations, logins)]
        return users


getter = Getter(client_id, client_secret)
users = getter.get_users()
users.sort(key=itemgetter(0), reverse=True)
for i in range(10):
    print(users[i])
