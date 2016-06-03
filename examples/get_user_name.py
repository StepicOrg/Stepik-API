import json
import requests


token = "..."

api_url = 'https://stepic.org/api/stepics/1'
resp = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).text)

user = resp['users']
name = user[0]['first_name'] +' ' + user[0]['last_name']

print(name)
