# Run with Python 3
# Count the number of countries known to Stepik!

import requests

# Copied from test_examples.py
client_id = "..."
client_secret = "..."

auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepik.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = resp.json()['access_token']

def get_data(page_id):
  api_url = 'https://stepik.org:443/api/countries?page={}'.format(page_id)
  response = requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).json()
  return response

count = 0
page_id = 0
response = {'countries': [], 'meta': {'has_next': True}}

# loop invariant: we've counted countries up to the current response including
while response['meta']['has_next']:
  page_id += 1
  response = get_data(page_id)
  count += len(response['countries'])

print('Seems like Stepik has knowledge about {} countries. Wow!'.format(count))
