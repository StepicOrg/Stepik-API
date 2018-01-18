# Run with Python 3

import json
import requests

# 1. Get your keys at https://stepik.org/oauth2/applications/ (client type = confidential, authorization grant type = client credentials)
client_id = '...'
client_secret = '...'

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepik.org/oauth2/token/', data={'grant_type': 'client_credentials'}, auth=auth)
token = json.loads(resp.text)['access_token']

# 3. Call API (https://stepik.org/api/docs/) using this token.
# Example:

# 3.1. Create a new lesson

api_url = 'https://stepik.org/api/lessons'
data = {
	'lesson': {
		'title': 'My Lesson'
	}
}
# Use POST to create new objects
r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=data)
lesson_id = r.json()['lessons'][0]['id']
print('Lesson ID:', lesson_id)
# You can also debug using:
# print(r.status_code) – should be 201 (HTTP Created)
# print(r.text) – should print the lesson's json (with lots of properties)

# 3.2. Add new theory step to this lesson

api_url = 'https://stepik.org/api/step-sources'
data = {
	'stepSource': {
		'block': {
			'name': 'text',
			'text': 'Hello World!'
		},
		'lesson': lesson_id,
		'position': 1
	}
}
r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=data)
step_id = r.json()['step-sources'][0]['id']
print('Step ID:', step_id)

# 3.3. Update existing theory step

api_url = 'https://stepik.org/api/step-sources/{}'.format(step_id)
data = {
	'stepSource': {
		'block': {
			'name': 'text',
			'text': 'Hi World!' # <-- changed here :)
		},
		'lesson': lesson_id,
		'position': 1
	}
}
# Use PUT to update existing objects
r = requests.put(api_url, headers={'Authorization': 'Bearer '+ token}, json=data)
step_id = r.json()['step-sources'][0]['id']
print('Step ID (update):', step_id)

# 3.4. Add new multiple (single) choice step to this lesson

api_url = 'https://stepik.org/api/step-sources'
data = {
	'stepSource': {
		'block': {
			'name': 'choice',
			'text': 'Pick one!',
			'source': {
				'options': [
					{'is_correct': False, 'text': '2+2=3', 'feedback': ''},
					{'is_correct': True,  'text': '2+2=4', 'feedback': ''},
					{'is_correct': False, 'text': '2+2=5', 'feedback': ''},
				],
				'is_always_correct': False,
				'is_html_enabled': True,
				'sample_size': 3,
				'is_multiple_choice': False,
				'preserve_order': False
			}
		},
		'lesson': lesson_id,
		'position': 2
	}
}
r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=data)
step_id = r.json()['step-sources'][0]['id']
print('Step ID:', step_id)

###

# Your lesson is ready!
print('--> Check https://stepik.org/lesson/{}'.format(lesson_id))

###

# 3.4. Create a new course

api_url = 'https://stepik.org/api/courses'
data = {
	'course': {
		'title': 'My Course'
	}
}
r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=data)
course_id = r.json()['courses'][0]['id']
print('Course ID:', course_id)

# 3.5. Add new module (section) to this course

api_url = 'https://stepik.org/api/sections'
data = {
	'section': {
		'title': 'My Section',
		'course': course_id,
		'position': 1
	}
}
r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=data)
section_id = r.json()['sections'][0]['id']
print('Section ID:', section_id)

# 3.6. Add your existing lesson to this section (it is called unit)

api_url = 'https://stepik.org/api/units'
data = {
	'unit': {
		'section': section_id,
		'lesson': lesson_id,
		'position': 1
	}
}
r = requests.post(api_url, headers={'Authorization': 'Bearer '+ token}, json=data)
unit_id = r.json()['units'][0]['id']
print('Unit ID:', unit_id)

###

# Your course is ready
print('--> Check https://stepik.org/course/{}'.format(course_id))

###
