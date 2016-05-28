import urllib.request
import json

req = urllib.request.Request('https://stepic.org/api/courses')
resp = urllib.request.urlopen(req).read().decode('utf-8')
obj = json.loads(resp)
courses = obj['courses']

titles = [course['title'] for course in courses]

x = []
for k in range(len(titles)):
    if titles[k].find('Python') != (-1):
        x.append(1)
    else:
        x.append(0)

if x.count(1) > x.count(0):
    a = 'больше'
else:
    a = 'меньше'

print('Курсов по Python ' + a + ', чем других.')
