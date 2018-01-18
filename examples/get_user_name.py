import json
import requests


token = "..."

api_url = 'https://stepik.org/api/stepics/1'  # should be stepic with "c"!
resp = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).text)

user = resp['users']
name = user[0]['first_name'] +' ' + user[0]['last_name']

print(name)
