import json
import requests

client_id = "EOjmCCXmEnowMfNneOYxiUzSZn6t69VUvoJwrqeY"
client_secret = "ILLPyh5c11TBqNdKdPBXau4i32uXIAYhOvFYmMObE8UzhatAIcdHjhPT178RgRnLpQ7wJ2SIljG5LYPfX5Iv4inYtu5z9jDzpPvN4y5LCCEU9sxzGkKCN0IgC3PLsHHv"

auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = json.loads(resp.text)['access_token']
api_url = 'https://stepic.org/api/courses?page='
pg = 1
i = 1
while True:
    course = json.loads(requests.get(api_url + str(pg), headers={'Authorization': 'Bearer '+ token}).text)
    for cs in course['courses']:
        print(str(i) + ". " + cs['title'])
        i = i + 1
    pg = pg + 1
    if(not course['meta']['has_next']):
        break