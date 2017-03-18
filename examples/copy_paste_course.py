# Run with Python 3
# Clone course from one Stepik instance (domain) into another
import re
import os
import csv
import ast
import json
import requests
import datetime

# Enter parameters below:
# 1. Get your keys at https://stepik.org/oauth2/applications/
# (client type = confidential, authorization grant type = client credentials)

client_id = '...'
client_secret = '...'
api_host = 'https://stepik.org'

# client_id = '...'
# client_secret = '...'
# api_host = 'http://127.0.0.1' # save to localhost 

course_id = 401
mode = 'SAVE' # IMPORTANT: use SAVE first, then use PASTE with uncommented (or changed) lines above (client keys and host)

cross_domain = True # to re-upload videos

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
response = requests.post('{}/oauth2/token/'.format(api_host),
                         data={'grant_type': 'client_credentials'},
                         auth=auth)
token = response.json().get('access_token', None)
if not token:
    print('Unable to authorize with provided credentials')
    exit(1)


# 3. Call API (https://stepik.org/api/docs/) using this token.
def fetch_object(obj_class, obj_id):
    api_url = '{}/api/{}s/{}'.format(api_host, obj_class, obj_id)
    response = requests.get(api_url,
                            headers={'Authorization': 'Bearer ' + token}).json()
    return response['{}s'.format(obj_class)][0]


def fetch_objects(obj_class, obj_ids):
    objs = []
    # Fetch objects by 30 items,
    # so we won't bump into HTTP request length limits
    step_size = 30
    for i in range(0, len(obj_ids), step_size):
        obj_ids_slice = obj_ids[i:i + step_size]
        api_url = '{}/api/{}s?{}'.format(api_host, obj_class,
                                         '&'.join('ids[]={}'.format(obj_id)
                                                  for obj_id in obj_ids_slice))
        response = requests.get(api_url,
                                headers={'Authorization': 'Bearer ' + token}
                                ).json()
        objs += response['{}s'.format(obj_class)]
    return objs


print('Mode:', mode)
print('Course ID:', course_id)
print()

if mode == 'SAVE': # SAVE TO DATA

    course = fetch_object('course', course_id)
    sections = fetch_objects('section', course['sections'])
    unit_ids = [unit for section in sections for unit in section['units']]
    units = fetch_objects('unit', unit_ids)
    lessons_ids = [unit['lesson'] for unit in units]
    lessons = fetch_objects('lesson', lessons_ids)
    step_ids = [step for lesson in lessons for step in lesson['steps']]
    steps = fetch_objects('step-source', step_ids)

    data = []

    idd = course['id']
    course = { key: course[key] for key in ['title', 'summary', 'course_format', 'language', 'requirements', 'workload', 'is_public', 'description', 'certificate', 'target_audience'] }
    row = ['course', idd, course]
    data.append(row)

    for section in sections:
        idd = section['id']
        section = { key: section[key] for key in ['title', 'position', 'course'] }
        row = ['section', idd, section]
        data.append(row)

    for unit in units:
        idd = unit['id']
        unit = { key: unit[key] for key in ['position', 'section', 'lesson'] }
        row = ['unit', idd, unit]
        data.append(row)

    for lesson in lessons:
        idd = lesson['id']
        lesson = { key: lesson[key] for key in ['title', 'is_public', 'language'] }
        row = ['lesson', idd, lesson]
        data.append(row)

    for step in steps:
        idd = step['id']
        step = { key: step[key] for key in ['lesson', 'position', 'block', 'cost'] }
        row = ['step-source', idd, step]
        data.append(row)
    
    # write data to file
    csv_file = open('course-{}-dump.csv'.format(course_id), 'w')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerows(data)
    csv_file.close()

    print('Objects:', len(data))

else: #PASTE FROM DATA

    # read data to file
    csv_file = open('course-{}-dump.csv'.format(course_id), 'r')
    csv_reader = csv.reader(csv_file)
    data = [row for row in csv_reader]
    for row in data:
        row[2] = ast.literal_eval(row[2]) # cast str to dict
        row[1] = int(row[1])
    csv_file.close()

    print('Objects:', len(data))
    print()

    courses_map = {}
    sections_map = {}
    lessons_map = {}

    for row in data:
        if row[0] != 'lesson':
            continue
        api_url = '{}/api/lessons'.format(api_host)
        api_data = { 'lesson' : row[2] }
        r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=api_data)
        new_id = r.json()['lessons'][0]['id']
        old_id = row[1]
        lessons_map[old_id] = new_id
        print('Lesson ID:', old_id, '-->', new_id)

    for row in data:
        if row[0] != 'step-source':
            continue
        # reupload video if needed
        if cross_domain and row[2]['block']['name'] == 'video':
            # find best video from the old step to upload it by url
            video_urls = row[2]['block']['video']['urls']
            best_quality = 0
            best_url = ''
            for url_and_quality in video_urls:
                q = int(url_and_quality['quality'])
                if q > best_quality:
                    best_quality = q
                    best_url = url_and_quality['url']
            api_url = '{}/api/videos'.format(api_host)
            api_data = {'source_url': best_url, 'lesson': lessons_map[row[2]['lesson']]}
            r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, data=api_data)
            new_id = r.json()['videos'][0]['id']
            old_id = row[2]['block']['video']['id']
            row[2]['block']['video']['id'] = new_id
            print('Video ID:', old_id, '-->', new_id)

        api_url = '{}/api/step-sources'.format(api_host)
        row[2]['lesson'] = lessons_map[row[2]['lesson']] # fix lesson id to new ones
        if cross_domain: # hack for attachements, only works for when source domain is stepik.org
            row[2]['block']['text'] = row[2]['block']['text'].replace('href="/media/attachments/', 'href="https://stepik.org/media/attachments/')
        api_data = { 'stepSource' : row[2] }
        r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=api_data)
        new_id = r.json()['step-sources'][0]['id']
        old_id = row[1]
        print('Step ID:', old_id, '-->', new_id)

    for row in data:
        if row[0] != 'course':
            continue
        api_url = '{}/api/courses'.format(api_host)
        api_data = { 'course' : row[2] }
        r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=api_data)
        new_id = r.json()['courses'][0]['id']
        old_id = row[1]
        courses_map[old_id] = new_id
        print('Course ID:', old_id, '-->', new_id)

    for row in data:
        if row[0] != 'section':
            continue
        api_url = '{}/api/sections'.format(api_host)
        row[2]['course'] = courses_map[row[2]['course']] # fix course id to new ones
        api_data = { 'section' : row[2] }
        r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=api_data)
        new_id = r.json()['sections'][0]['id']
        old_id = row[1]
        sections_map[old_id] = new_id
        print('Section ID:', old_id, '-->', new_id)

    for row in data:
        if row[0] != 'unit':
            continue
        api_url = '{}/api/units'.format(api_host)
        row[2]['section'] = sections_map[row[2]['section']] # fix section id to new ones
        row[2]['lesson'] = lessons_map[row[2]['lesson']] # fix lesson id to new ones
        api_data = { 'units' : row[2] }
        r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=api_data)
        new_id = r.json()['units'][0]['id']
        old_id = row[1]
        print('Unit ID:', old_id, '-->', new_id)

    print()
    print(courses_map)
    
print()
print('Done!')
