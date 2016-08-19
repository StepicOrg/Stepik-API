# Run with Python 3
import collections
import json
import operator
import requests
import urllib

# 1. Get your keys at https://stepik.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = "..."
client_secret = "..."

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post(
    'https://stepik.org/oauth2/token/',
    data={'grant_type': 'client_credentials'},
    auth=auth
)
response = json.loads(resp.text)
token = response.get('access_token')

if not token:
    print('Auth unsuccessful')
    exit(0)


# 3. Call API (https://stepik.org/api/docs/) using this token.
# Example:

def load_api(method, **kwargs):
    api_url = 'https://stepik.org:443/api/'
    params = urllib.parse.urlencode(kwargs)
    return json.loads(requests.get(
        api_url + method + '/?' + params,
        headers={'Authorization': 'Bearer ' + token}).text
    )

# Get top lessons by reaction on recommendations

NUM_OF_REACTION_PAGES = 100
NUM_OF_REACTION_TOP = 10

lessons_method = 'lessons'
recommendation_reactions_method = 'recommendation-reactions'


def print_status(message, done, total):
    print('{}: {}/{}'.format(message, done, total), end='\r' if done != total else '\n')

course_reactons = collections.defaultdict(int)

for i in range(NUM_OF_REACTION_PAGES):
    print_status('Loading', i+1, NUM_OF_REACTION_PAGES)
    response = load_api(recommendation_reactions_method, page=i+1)

    for reaction in response.get('recommendation-reactions'):
        value = reaction.get('reaction')
        course_reactons[reaction.get('lesson')] += value if value > 0 else -value - 1

    if not response.get('meta').get('has_next'):
        break


sorted_lessons = sorted(course_reactons.items(), key=operator.itemgetter(1), reverse=True)

# Add all equal to the last
while len(sorted_lessons) > NUM_OF_REACTION_TOP and \
      sorted_lessons[NUM_OF_REACTION_TOP][1] == sorted_lessons[NUM_OF_REACTION_TOP - 1][1]:
    NUM_OF_REACTION_TOP += 1

print('Top lessons by reaction')
print('(Title: reaction value)')
print()

for lesson_id in sorted_lessons[:min(NUM_OF_REACTION_TOP, len(sorted_lessons))]:
    response = response = load_api('{}/{}'.format(lessons_method, lesson_id[0]))
    lesson = response.get('lessons')[0]

    print('{}: {}'.format(lesson.get('title'), lesson_id[1]))
