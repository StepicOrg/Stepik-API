# Run with Python 3
import requests
from pprint import pprint

# Enter parameters below:
# 1. Get your keys at https://stepik.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
CLIENT_ID = '...'
CLIENT_SECRET = '...'
API_HOST = 'https://stepik.org'

# 2. Get a token
AUTH = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
RESP = requests.post('https://stepik.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=AUTH
                     )
TOKEN = RESP.json()['access_token']


def prepare_ids(ids):
    request = ''
    for id in ids:
        request += 'ids[]={}&'.format(id)
    return request[:-1]


def api_call(relative_url):
    api_url = API_HOST + ':443/api/' + relative_url
    data = requests.get(api_url, headers={'Authorization': 'Bearer ' + TOKEN})
    return data


def get_leaders():
    data = api_call('leaders')
    return data.json()['leaders']


def get_users(user_ids):
    request = prepare_ids(user_ids)
    data = api_call('users?{}'.format(request))
    return data.json()['users']


def get_social_profiles(social_ids):
    if not social_ids:
        return None
    request = prepare_ids(social_ids)
    data = api_call('social-profiles?{}'.format(request))
    profiles = data.json()['social-profiles']
    accounts = {}
    for profile in profiles:
        accounts[profile['provider']] = profile['url']
    return accounts


def main():
    leaders = get_leaders()
    users = []
    while leaders:
        IDS_PER_REQUEST = 10
        ids = [u['user'] for u in leaders[:IDS_PER_REQUEST]]
        leaders = leaders[IDS_PER_REQUEST:]
        users += get_users(ids)

    result = []

    for index, user in enumerate(users):
        acc = get_social_profiles(user['social_profiles'])
        if acc:
            print('download data for ' + str(index + 1))
            name = user['first_name']
            if user['last_name']:
                name += ' ' + user['last_name']
            result.append([index + 1, name, acc])

    pprint(result)


if __name__ == '__main__':
    main()
