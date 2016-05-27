
# coding: utf-8

# In[13]:

import json
import requests
from operator import itemgetter


# In[14]:

client_id = "w6MarcVX2yhRZDgTdOqrGr0jR1hbLwMTUXiCSQyU"
client_secret = "SlfCAqMZCtZlCl1N96zCc4hmQ08IhuzEfzstkXY7LTfgDfGxvo0z6csfPC9aWPPbVV68OLpu3yY4K8EMRBIFeE8mvtsqse3ISmjzn1qasP6c44nx2DdcskliNyFpPngW"

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )


# In[15]:

token = json.loads(resp.text)['access_token']


# In[16]:

page = 1


# In[17]:

api_url = 'https://stepic.org/api/users?page=' + str(page);


# In[18]:

result = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).text)


# In[19]:

#print(users)


# In[25]:

indices = []
names = []


# In[12]:

while(result['meta']['has_next'] == True):
    page += 1
    profiles = result['users']
    for profile in profiles:
        indices.append(profile['reputation'])
        name = profile['first_name'] + " " + profile['last_name']
        names.append(name)
        api_url = 'https://stepic.org/api/users?page=' + str(page);
        result = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer '+ token}).text)
    #print(users)


# In[27]:

users = [list(c) for c in zip(indices, names)]


# In[28]:

print(users)


# In[32]:

users.sort(key=itemgetter(0), reverse=True)


# In[33]:

for i in range(10):
    print(users[i])


# In[ ]:



