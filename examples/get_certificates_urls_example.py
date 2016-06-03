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

def get_certificates_by_course(links, page_number):
    api_url = 'https://stepic.org/api/courses?page={}'.format(page_number)
    courses = requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).json()

    for i in courses['courses']:
        link = i['certificate_link']
        if link:
            links.append('https://stepic.org{}'.format(link))

    return courses['meta']['has_next']


def print_certificate_links():
    has_next = True
    page = 1
    links = []

    while(has_next):
        has_next = get_certificates_by_course(links, page)
        page += 1

    for link in links:
        print(link)


print_certificate_links()

