'''
Niema Moshiri 2016
Download a Stepik course
Run with Python 3
'''
USAGE = "USAGE: python DownloadStepikCourse.py <course_ID>"
# imports
import sys
import requests
import json
import os
import datetime

# Enter parameters below:
# Get your keys at https://stepik.org/oauth2/applications/
# (client type = confidential, authorization grant type = client credentials)
client_id = ...
client_secret = ...
api_host = 'https://stepik.org'

# parse args (to get course ID)
if len(sys.argv) != 2:
    print("\nERROR: Incorrect number of arguments")
    print(USAGE)
    exit(-1)
try:
    course_id = int(sys.argv[1])
except:
    print("\nERROR: Course ID was not an integer")
    print(USAGE)
print("Attempting to download course: " + str(course_id))

# Get a token
print("Requesting token...")
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
response = requests.post('https://stepik.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth)
if "503" in str(response):
    print("\nERROR: Received 503 error from Stepik")
    print("Perhaps they are doing maintenance? Check Stepik and try again later")
    exit(-1)
token = response.json().get('access_token', None)
if not token:
    print("\nERROR: Unable to authorize with provided credentials")
    print("Client ID:     " + str(client_id))
    print("Client Secret: " + str(client_secret))
    exit(-1)
print("Token requested successfully\n")

# Call API (https://stepik.org/api/docs/) to download a single object
def fetch_object(obj_class, obj_id):
    api_url = '{}/api/{}s/{}'.format(api_host, obj_class, obj_id)
    response = requests.get(api_url,
                            headers={'Authorization': 'Bearer ' + token}).json()
    return response['{}s'.format(obj_class)][0]

# Fetch all objects
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

# Perform the fetches
course = fetch_object('course', course_id)
sections = fetch_objects('section', course['sections'])
print("Ready to download course: " + course['title'])

unit_ids = [unit for section in sections for unit in section['units']]
units = fetch_objects('unit', unit_ids)

lesson_ids = [unit['lesson'] for unit in units]
lessons = fetch_objects('lesson', lesson_ids)

step_ids = [step for lesson in lessons for step in lesson['steps']]
steps = fetch_objects('step', step_ids)

for secIndex, section in enumerate(sections):
    print("===== BEGIN SECTION " + str(secIndex+1) + " OF " + str(len(sections)) + " =====")
    unit_ids = section['units']
    units = fetch_objects('unit', unit_ids)

    for unitIndex, unit in enumerate(units):
        if unitIndex > 0:
            print()
        print("--- Downloading Unit " + str(unitIndex+1) + " of " + str(len(units)) + " ---")
        lesson_id = unit['lesson']
        lesson = fetch_object('lesson', lesson_id)

        step_ids = lesson['steps']
        steps = fetch_objects('step', step_ids)

        for stepIndex, step in enumerate(steps):
            print("Downloading step " + str(stepIndex+1) + " of " + str(len(steps)) + "...")
            step_source = fetch_object('step-source', step['id'])
            path = [
                '{} {}'.format(str(course['id']).replace('/','-').zfill(2), course['title']),
                '{} {}'.format(str(section['position']).replace('/','-').zfill(2), section['title']),
                '{} {}'.format(str(unit['position']).replace('/','-').zfill(2), lesson['title']),
                '{}_{}_{}.step'.format(lesson['id'], str(step['position']).zfill(2), step['block']['name'])
                ]
            try:
                os.makedirs(os.path.join(os.curdir, *path[:-1]))
            except:
                pass
            filename = os.path.join(os.curdir, *path)
            f = open(filename, 'w')
            data = {
                'block': step_source['block'],
                'id': str(step['id']),
                'time': datetime.datetime.now().isoformat()
            }
            f.write(json.dumps(data))
            f.close()
            print(filename)
    print("===== END SECTION " + str(secIndex+1) + " OF " + str(len(sections)) + " =====\n\n")