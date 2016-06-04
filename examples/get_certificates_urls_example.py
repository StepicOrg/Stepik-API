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
token = resp.json()['access_token']

# 3. Call API (https://stepic.org/api/docs/) using this token.
# Example:

def get_user_id():
    api_url = 'https://stepic.org/api/stepics/1'
    user = requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).json()
    return user['users'][0]['id']


def print_certificates(page_number):
    id = get_user_id()
    api_url = 'https://stepic.org/api/certificates?user={}&page={}'.format(id, page_number)
    certificate = requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).json()

    for i in certificate['certificates']:
        print(i['url'])

    return certificate['meta']['has_next']


def print_certificate_links():
    has_next = True
    page = 1

    while(has_next):
        has_next = print_certificates(page)
        page += 1


print_certificate_links()
