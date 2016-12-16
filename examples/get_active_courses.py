# Script that produces: 
# a) courses, started in the last six months, in which there are new lessons in the last month,
# b) courses created over the past six months, in which more than 10 students
#
# Issues (stdout + csv file):
# 0) the condition a) or b) or a) + b)
# 1) a reference to the course
# 2) the name of the course
# 3) name of the author of the course
# 4) the course author email

import csv
import json
import requests
import datetime
from dateutil import parser

def get_token():
    # Get your keys at https://stepic.org/oauth2/applications/
    # (client type = confidential, authorization grant type = client credentials)
    client_id = '...'
    client_secret = '...'

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepik.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth)
    token = json.loads(resp.text)['access_token']
    return token


def get_data(pageNum):
    api_url = 'https://stepik.org/api/courses?page={}'.format(pageNum)
    course = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + get_token()}).text)
    return course

 
limit_6m = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=31*6)
limit_1m = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=31)

def get_courses():
    page = 1
    while True:
        api_url = 'https://stepik.org/api/courses?page={}'.format(page)
        courses = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + get_token()}).text)['courses']
        for course in courses:
            if parser.parse(course['create_date']) < limit_6m:
                return
            # a) courses, started in the last six months, in which there are new lessons in the last month
            a = ''
            api_url = 'https://stepik.org/api/lessons?course={}&order=-id'.format(course['id'])
            lessons = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + get_token()}).text)['lessons']
            if lessons and parser.parse(lessons[0]['create_date']) > limit_1m:
                a = 'A'
            # b) courses created over the past six months, in which more than 10 students
            b = ''
            api_url = 'https://stepik.org/api/members?group={}'.format(course['learners_group'])
            members = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + get_token()}).text)['members']
            if len(members) > 10:
                b = 'B'
            # Issues a row
            if a or b:
                owner = course['owner']
                api_url = 'https://stepik.org/api/users/{}'.format(owner)
                user = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + get_token()}).text)['users'][0]
                owner_name = user['first_name'] + ' ' + user['last_name']
                api_url = 'https://stepik.org/api/email-addresses?user={}&is_primary=true'.format(owner)
                owner_email = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + get_token()}).text)['email-addresses'][0]['email']
                link = 'https://stepik.org/{}'.format(course['id'])
                row = [a, b, link, course['title'], owner_name, owner_email]
                yield row
        page += 1

csv_file = open('get_active_courses-{}.csv'.format(datetime.date.today()), 'w')
csv_writer = csv.writer(csv_file)

header = ['A?', 'B?', 'Link', 'Title', 'Owner', 'OwnerEmail']
csv_writer.writerow(header)
print('\t'.join(header))

for row in get_courses():
    csv_writer.writerow(row)
    print('\t'.join(row))

csv_file.close()