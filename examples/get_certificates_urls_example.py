# Run with Python 3
import requests

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
# Example:


def get_user_id():
    api_url = 'https://stepik.org/api/stepics/1'  # should be stepic with "c"!
    user = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).json()
    return user['users'][0]['id']


def get_certificates(page_number):
    user_id = get_user_id()
    api_url = 'https://stepik.org/api/certificates?user={}&page={}'.format(user_id, page_number)
    page = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).json()

    for certificate in page['certificates']:
        links.append(certificate['url'])

    return page['meta']['has_next']


def get_certificate_links():
    has_next = True
    page = 1

    while has_next:
        has_next = get_certificates(page)
        page += 1


links = []
get_certificate_links()

with open('certificates.html', 'w', encoding='utf-8') as f:
    f.write('<html> \n')
    f.write('<head> \n')
    f.write('<title> Certificates </title> \n')
    f.write('<style> ol { line-height: 1.5; } </style> \n')
    f.write('</head> \n')
    f.write('<body> \n')
    f.write('<h1> Certificates </h1> \n')
    f.write('<ol> \n')

    for url in links:
        f.write('<li><a href="{}">{}</a></li> \n'.format(url, url))

    f.write('</ol> \n')
    f.write('</body> \n')
    f.write('</html> \n')
