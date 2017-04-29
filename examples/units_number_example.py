import json
import requests

client_id = "n4mnzQGfDEfOhFixwBvLV2mZJJLvf86pzfMMiPF5"
client_secret = "40ON9IPJRDAngUkVbGBTEjCBAwc2wB7lV8e71jJUPKabdKq6KBTUBKb1xGkh82KtAI1AqISrL3Zi4sTfhCBVh27YvlV6Y5klpXXV5loUWvuhMSRiN3HRZzVDO0fLBibv"

auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = json.loads(resp.text)['access_token']


def number_of_units(page_num):
    api_url = 'https://stepic.org/api/courses/{}'.format(page_num)
    course = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).text)
    if "courses" in course.keys():
        fields = course["courses"][0]
        curse_name = fields["slug"]
        course_units = "consists from {} units".format(fields["total_units"])
        print(" ".join([curse_name, course_units]))

for i in range(71):
    number_of_units(i)
