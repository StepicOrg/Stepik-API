
import json
import requests

client_id = "..."
client_secret = "..."

class StepicAPI(object):
    def __init__(self, client_id, client_secret):
        self.api_url = 'https://stepic.org/api/'
        
        self.client_id = client_id
        self.client_secret = client_secret
        
        try:
            auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
            resp = requests.post('https://stepic.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth
                         )
            self.token = json.loads(resp.text)['access_token']
        except:
            print("Error while obtaining token")
      
    def get(self, url):
        try:
            resp = json.loads(requests.get(url, headers={'Authorization': 'Bearer ' + self.token}).text)
        except:
            print("Error while getting data")
            resp = None
        return resp
     
    # announcements
    def announcements(self, page = 1):
        url = self.api_url + 'announcements?page=%d'%page 
        return self.get(url)
    def announcements_pk(self, pk):
        url = self.api_url + 'announcements/%d'%pk 
        return self.get(url)
    
    # 
    def course_subscriptions(self, page = 1):
        url = self.api_url + 'course-subscriptions?page=%d'%page
        return self.get(url)
    def course(self, course_id):
        url = self.api_url + 'courses/%d'%course_id
        return self.get(url)
    
        
sapi = StepicAPI(client_id, client_secret)
#Пример получения списка курсов

has_next = True
page = 0
course_ids = []
while has_next:
    page += 1
    courses = sapi.course_subscriptions(page)
    has_next = courses['meta']['has_next']
    for el in courses['course-subscriptions']:
        course_ids.append(el['course'])
print("pages: %d"%page)    
print("course ids: %s"%str(course_ids))

#Для каждого курса получим информацию о нем
data = []
for course_id in course_ids:
    course_data = sapi.course(course_id)
    summary = (course_data['courses'][0]['summary'])
    title = (course_data['courses'][0]['title'])
    data.append((course_id, title, summary))
print(data)
