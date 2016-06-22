import requests

client_id = "..."
client_secret = "..."
try:
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret);
    resp = requests.post('https://stepic.org/oauth2/token/', data={'grant_type': 'client_credentials'},auth=auth)
    token = resp.json()['access_token']
except:
    print('problems getting token')
api_url = "https://stepic.org/api/";

author_courses = {}
page_ind = 1

print('Please, wait a bit while list of courses is being processed')
# in this cycle we get all courses' titles and their authors
while True:
    page = requests.get(api_url + 'courses' + '?page=' + str(page_ind) + '&language=ru', headers={'Authorization': 'Bearer ' + token}).json()
    for course in page['courses']:
        # ignore 'dead' courses
        if course['discussions_count'] == 0:
            continue
        for author in course['authors']:
            if not author in author_courses:
                author_courses.update({author : set()})

            # for each author we will have all courses that were created with his participation
            author_courses[author].add(course['title'])
    if not page['meta']['has_next']:
        break
    page_ind += 1

for user_id,titles in author_courses.items():
    user = requests.get(api_url + 'users/' + str(user_id)).json()['users'][0]
    print()
    print(user['first_name'], user['last_name'], 'took part in creating ', end='')
    if len(titles) == 1:
        print('this course:')
    else:
        print('these courses:')
    for title in titles:
        print(title)
