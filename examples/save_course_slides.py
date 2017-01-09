# Run with Python3
# Saves all presentations from course in pdfs and arranges them into folders
# BeautifulSoup is required, just do:  pip install beautifulsoup4

import requests
import sys
import os
from bs4 import BeautifulSoup

client_id = "..."
client_secret = "..."
api_host = "https://stepik.org/"

auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
response = requests.post('https://stepik.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth)
token = response.json().get('access_token', None)
if not token:
    print('Unable to authorize with provided credentials')
    exit(1)

course_id = 0

if len(sys.argv) == 2:
    course_id = sys.argv[1]
else:
    print("Error, enter course_id")
    exit(0)


# get 1 json object
def fetch_object(obj_class, obj_id):
    api_url = '{}/api/{}s/{}'.format(api_host, obj_class, obj_id)
    response = requests.get(api_url,
                            headers={'Authorization': 'Bearer ' + token}).json()
    return response['{}s'.format(obj_class)][0]


# get json-objects with ids in right order
def fetch_objects(obj_class, obj_ids, keep_order=True):
    objs = []
    # Fetch objects by 30 items,
    # so we won't bump into HTTP request length limits
    step_size = 30
    for i in range(0, len(obj_ids), step_size):
        obj_ids_slice = obj_ids[i:i + step_size]
        print(obj_ids_slice)
        api_url = '{}/api/{}s?{}'.format(api_host, obj_class,
                                         '&'.join('ids[]={}'.format(obj_id)
                                                  for obj_id in obj_ids_slice))

        response = requests.get(api_url,headers={'Authorization': 'Bearer ' + token}).json()

        objs += response['{}s'.format(obj_class)]
    if (keep_order):
        return sorted(objs, key=lambda x: obj_ids.index(x['id']))
    return objs


# convert name of section into proper name folder
def replace_characters(text):
    text = text.replace(":", " -")
    text = text.replace("?", " ")
    return text


# download pdf
def download_file(link, path):
    slides = requests.get(link)
    file_name = link[link.rfind('/') + 1:]
    with open(os.path.join(path, file_name), "wb") as pdf:
        for chunk in slides.iter_content(chunk_size=128):
            pdf.write(chunk)


# find all links with slides
def find_slides(text, path):
    soup = BeautifulSoup(text, 'html.parser')
    for link in soup.find_all('a'):
        if link.get('href') and "slides" in link.get('href'):
            print("https://stepik.org" + link.get('href'))
            download_file("https://stepik.org" + link.get('href'), path)

course = fetch_object("course", course_id)
print(course['sections'])
sections = fetch_objects("section", course['sections'])

title = course['title']
workload = course['workload']
summary = course['summary']

#create info dir
current_path = os.path.dirname(os.path.abspath(__file__))
current_path = os.path.join(current_path, title)

if not os.path.exists(current_path):
    os.makedirs(current_path)
    with open(os.path.join(current_path, "readme.html"), "w") as info_file:
        print(
            "<h1>" + title + "</h1>" + "<p><b>Нагрузка</b>: " + workload + "</p>" + "<b>Коротко о курсе</b>: " + summary,
            file=info_file)
else:
    print("folder already exists")

for section in sections:
    if not os.path.exists(os.path.join(current_path, replace_characters(section['title']))):
        os.makedirs(os.path.join(current_path, replace_characters(section['title'])))


    units_id = section['units']
    units = fetch_objects('unit', units_id)

    for unit in units:
        lesson = fetch_object('lesson', unit['lesson'])
        steps = fetch_objects('step', lesson['steps'])
        for step in steps:
            text = step['block']['text']
            path = os.path.join(current_path, section['title'])
            find_slides(text, path)