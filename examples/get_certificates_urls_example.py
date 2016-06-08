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
    user = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).json()
    return user['users'][0]['id']


def get_certificates(page_number):
    user_id = get_user_id()
    api_url = 'https://stepic.org/api/certificates?user={}&page={}'.format(user_id, page_number)
    certificate = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).json()

    for i in certificate['certificates']:
        links.append(i['url'])

    return certificate['meta']['has_next']


def get_certificate_links():
    has_next = True
    page = 1

    while has_next:
        has_next = get_certificates(page)
        page += 1


links = []
get_certificate_links()

f = open('certificates.html', 'w', encoding='utf-8')

begin = """<html>
<head><title> Certificates </title>
<style>
   ol {
    line-height: 1.5;
   }
</style>
</head>
<body>
<h1> Certificates </h1>
<ol>
"""

end = """</ol>
</body>
</html>"""

f.write(begin)
for url in links:
    f.write('<li><a href="{}">{}</a></li> \n'.format(url, url))
f.write(end)
f.close()
