# Run with Python3
# Saves all presentations from course in pdfs and arranges them into folders
# BeautifulSoup is required, just do:  pip install beautifulsoup4

import requests
import sys
import os
from bs4 import BeautifulSoup
import urllib.request
import urllib.response

client_id = "..."
client_secret = "..."
api_host = "https://stepik.org/api/"


# get a token
def auth():
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    response = requests.post('https://stepik.org/oauth2/token/',
                             data={'grant_type': 'client_credentials'},
                             auth=auth)
    global token
    token = response.json().get('access_token', None)
    if not token:
        print('Unable to authorize with provided credentials')
        exit(1)


# get 1 json object
def fetch_object(obj_class, obj_id):
    api_url = "{}/{}s/{}".format(api_host, obj_class, obj_id)
    response = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).json()
    return response["{}s".format(obj_class)][0]


# get json-objects with ids
def fetch_objects(obj_class, ids):
    objs = []
    step_size = 30
    for i in range(0, len(ids), step_size):
        cur_ids = ids[i:i + step_size]
        api_url = "{}/{}s/?".format(api_host, obj_class)
        for id in cur_ids:
            api_url += "ids[]={}&".format(id)
        response = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).json()
        objs += response["{}s".format(obj_class)]
    return objs


# convert name of section into proper name folder
def replace_characters(text):
    text = text.replace(":", " -")
    text = text.replace("?", " ")
    return text


# create folder of course with readme.html about course
def create_info_dir(title, workload, summary):
    current_path = os.path.dirname(os.path.abspath(__file__))
    global CURRENT_PATH

    current_path = os.path.join(current_path, title)
    CURRENT_PATH = current_path
    if not os.path.exists(current_path):
        os.makedirs(current_path)
        with open(os.path.join(current_path, "readme.html"), "w") as info_file:
            print(
                "<h1>" + title + "</h1>" + "<p><b>Нагрузка</b>: " + workload + "</p>" + "<b>Коротко о курсе</b>: " + summary,
                file=info_file)
    else:
        print("folder already exists")

# create folder for section
def create_folder(title):
    if not os.path.exists(os.path.join(CURRENT_PATH, title)):
        os.makedirs(os.path.join(CURRENT_PATH, title))


# download pdf
def download_file(link, path):
    slides = urllib.request.urlopen(link)
    file_name = link[link.rfind('/') + 1:]
    global count_slides
    with open(os.path.join(path, file_name), "wb") as pdf:
        while (True):
            data = slides.read(4096)
            if data:
                pdf.write(data)
            else:
                break
    count_slides += 1


# find all links with slides
def find_slides(text, path):
    soup = BeautifulSoup(text, 'html.parser')
    for link in soup.find_all('a'):
        if link.get('href') and "slides" in link.get('href'):
            print("https://stepik.org" + link.get('href'))
            download_file("https://stepik.org" + link.get('href'), path)


def get_course_info(id):
    course = fetch_object("course", id)
    sections = fetch_objects("section", course['sections'])

    title = course['title']
    workload = course['workload']
    summary = course['summary']
    create_info_dir(title, workload, summary)

    for section in sections:
        create_folder(replace_characters(section['title']))

        units_id = section['units']
        units = fetch_objects('unit', units_id)

        for unit in units:
            lesson = fetch_object('lesson', unit['lesson'])
            steps = fetch_objects('step', lesson['steps'])
            for step in steps:
                text = step['block']['text']
                path = os.path.join(CURRENT_PATH, section['title'])
                find_slides(text, path)


def main():
    auth()
    course_id = 0
    if len(sys.argv) == 2:
        course_id = sys.argv[1]
    else:
        print("Error, enter course_id")
        exit(0)
    global count_slides
    count_slides = 0
    get_course_info(course_id)


if __name__ == "__main__":
    main()
