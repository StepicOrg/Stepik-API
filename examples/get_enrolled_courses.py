# coding=utf-8

import requests

# Enter parameters below:
# 1. Get your keys at https://stepik.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = '...'
client_secret = '...'
api_host = 'https://stepik.org'

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepik.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = resp.json().get('access_token')
if not token:
    raise RuntimeWarning('Client id/secret is probably incorrect')


# 3. Call API (https://stepik.org/api/docs/) using this token.
# Generator definition for iterating over pages
def list_pages(api_url, obj_class):
    has_next = True
    page = 1
    if '?' in api_url:
        connector = '&'
    else:
        connector = '?'
    while has_next:
        response = requests.get(api_url + '{}page={}'.format(connector, page),
                                headers={'Authorization': 'Bearer ' + token}).json()
        yield response[obj_class]
        page += 1
        has_next = response['meta']['has_next']


# Access to any API method
def fetch_object(obj_class, query_string=''):
    api_url = '{}/api/{}{}'.format(api_host, obj_class, query_string)
    response = list_pages(api_url, obj_class)
    return [obj for page in response for obj in page]       # Example of using generator


# Information about course sections
def get_sections(course_sections):
    qs = '?ids[]=' + '&ids[]='.join([str(cs) for cs in course_sections])    # Example of multiple IDs call
    sections = fetch_object('sections', qs)
    return sections


# Information about enrolled courses
def get_enrolled_courses():
    courses = fetch_object('courses', '?enrolled=true')
    for course in courses:
        course['sections'] = get_sections(course['sections'])
    return courses


# Retrieving course information
courses = get_enrolled_courses()

# and HTML-report generating
with open('enrolled_courses.html', 'w', encoding='utf-8') as f:
    f.write('<html>')
    f.write('<head>')
    f.write('<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">')
    f.write('<title>Courses enrolled by user</title>')
    f.write('</head>')
    f.write('<body>')
    for course in courses:
        f.write('<h1><a href="https://stepik.org/course/{0}">{1}</a></h1>'.format(course['slug'], course['title']))
        f.write('<p>{}</p>'.format(course['summary']))
        if course['sections']:
            f.write('<p>Course sections: </p>')
            f.write('<ul>')
            for section in course['sections']:
                f.write('<li>{}</li>'.format(section['title']))
            f.write('</ul>')
        f.write('<hr>')
    f.write('</body>')
    f.write('</html>')
