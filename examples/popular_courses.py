# Run with Python 3
import json
import requests

### DATA ENDS
# Enter parameters below:
# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = '...'
client_secret = '...'
api_host = 'https://stepik.org'

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = resp.json().get('access_token')
if not token:
    raise RuntimeWarning('Client id/secret is probably incorrect')


# 3. Call API (https://stepic.org/api/docs/) using this token.
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

# SOMETHING MEANINGFUL:

courses = fetch_objects('course', list(range(2000)))

total_courses = 0
total_enrollments = 0
total_lessons = 0

for course in courses:
    course_id = course['id']
    learners_group_id = course['learners_group']
    learners_group = fetch_object('group', learners_group_id)
    learners_count = len(learners_group['users'])
    sections = fetch_objects('section', course['sections'])
    units_count = sum(len(section['units']) for section in sections)
    lessons_count = units_count
    print(course_id, learners_count, lessons_count)
    if learners_count >= 10:
        total_courses += 1
        total_enrollments += learners_count
        total_lessons += lessons_count

print('Number of courses with >= 10 learners:', total_courses)
print('Total number of enrollments in such courses:', total_enrollments)
print('Total number of lessons in such courses:', total_lessons)