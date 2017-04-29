__author__ = 'JuriaSan'

import requests


max_users_num = 50
count = 0
page_num = 0
has_next = True
users = []
stop = False
while not stop and has_next:
    page_num += 1
    url = 'https://stepic.org/api/users'.format(page_num)
    request = requests.get(url).json()
    users = request['users']
    has_next = request['meta']['has_next']
    for user in users:
        if len(users) >= max_users_num:
            stop = True
            break
        else:
            users.append(user)
            print (user['first_name'], user['last_name'])


