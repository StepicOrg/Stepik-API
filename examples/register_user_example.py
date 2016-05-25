import requests

URL = 'https://stepic.org/accounts/signup/?next=/'
client = requests.session()


# Retrieve the CSRF token first
client.get(URL)
csrftoken = client.cookies['csrftoken']


# Register User
# Put all credentials here
user_email = "..."
first_name = "..."
last_name = "..."
password = "..."
login_data = dict(first_name=last_name, last_name=last_name,
                  email=user_email, password1=password, password2=password)
login_data['csrfmiddlewaretoken'] = csrftoken
login_data['next'] = '/'
response = client.post(URL, data=login_data, headers=dict(Referer=URL))


# Login User and obtain csrf token
csrftoken = client.cookies['csrftoken']
URL = 'https://stepic.org/accounts/login/'
loginresp = client.post(URL, data={'csrfmiddlewaretoken': csrftoken, 'login': user_email,
                                                               'password': password}, headers=dict(Referer=URL))
csrftoken = client.cookies['csrftoken']
