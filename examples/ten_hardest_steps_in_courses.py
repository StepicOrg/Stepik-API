# Run with Python 3
import requests

# 1. Get your keys at https://stepic.org/oauth2/applications/ (client type = confidential,
# authorization grant type = client credentials)
client_id = ""
client_secret = ""

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = resp.json()['access_token']


# 3. Call API (https://stepic.org/api/docs/) using this token.
# Just For Example
courses = ['117', '658']


def fetch_course(course, page):
    url = 'https://stepic.org:443/api/course-grades?page={}&course={}'.format(page, course)
    return requests.get(url, headers={'Authorization': 'Bearer '+ token}).json() 


def scores_per_course(course):
    # init
    page = 1
    response = fetch_course(course, page)
    it = response['course-grades'][0]['results']
    names = sorted([i for i in it])
    scores = [(0, it[name]['step_id']) for name in names]
    
    while response['meta']['has_next']:
        response = fetch_course(course, page)
        for row in response['course-grades']:
            it = row['results']
            scores = [(score[0] + 1 if it[name]['is_passed'] else score[0], it[name]['step_id']) for name, score in zip(names, scores)]
        page += 1
    return scores

scores = []
for course in courses:
    scores += [scores_per_course(course)]
    
import pylab
for scr in scores:
    pylab.plot([v[0] for v in scr])

pylab.show()


final = []
for course in scores: 
    final += course

hardest = sorted(final)[0:10]
print(hardest)
