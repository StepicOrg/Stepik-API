[![Build Status](https://travis-ci.org/StepicOrg/stepic-api-docs.svg?branch=master)](https://travis-ci.org/StepicOrg/stepic-api-docs)

<h4>Stepic.org API overview</h4>

### Overview
Stepic.org uses REST API in JSON format. 

All the endpoints listed at <a href="https://stepic.org/api/docs">https://stepic.org/api/docs</a><br>
It's also possible to test requests on that url. Methods from `/api/docs` are restricted only to `GET` requests.

The most part of Stepic.org is written as single-page application using Ember.js framework, and all the interactions<br>
with content are done using API. Currently few operations are still unsupported through API.

### Basic
###### Flat
Stepic api schema if flat, meaning there is no multi-level end-points.

Every request return list of objects, even if only one object was asked. List can contain 0 or more elements.

For example response `from https://stepic.org/api/courses/1`have not one course object, but array, containing one course object.

###### Pagination
All responses from GET are 1)paginated 2)have extra `meta` object with extra information about pagination. For example:
```{
    meta: {
        page: 1,
        has_next: true,
        has_previous: false
    },
    requested_objects: [...]
}```<br>
If next page exists, it can be requested using Query parameters: `page=...`, by default, if no query given, it's equal to 1:

`https://stepic.org/api/courses` is equal to `https://stepic.org/api/courses?page=1`<br>
next page: `https://stepic.org/api/courses?page=2` and so on.

Usual page size is equal to 20 elements, but it can vary due to permission, api endpoint or other cases.<br>
We <b>do not recommend to rely on constant page size</b>, instead, pagination size should always be calculated after response.

###### Side-Loading
Response may also contain multiple related objects. For example, for registered user, request to `https://stepic.org/api/courses`  also include user course `enrollments`. 


###### OAuth 2
For using Stepic.org API as registered uses, OAuth2 authorization needed.
First you should register your application at `https://stepic.org/oauth2/applications/` while being logged in and obtain application keys.
You can also set `redirect_uri`, `Client type` and `Authorization grant type` there.

Authorization endpoint (Authorization code, Implicit grant; redirect_uri needed): <br>`https://stepic.org/oauth2/authorize/.`<br>

Token endpoint (Authorization code, Password и Client credentials):<br> `https://stepic.org/oauth2/token/`.


###### Client credentials flow
You can than obtain access token using this client credential flow:<br>

 `curl -X POST -d "grant_type=client_credentials" -u"CLIENT_ID:CLIENT_SECRET" https://stepic.org/oauth2/token/`<br>


Response: 

`{"access_token": "ACCESS_TOKEN", "scope": "read write", "expires_in": 36000, "token_type": "Bearer"}`

Example with access token:

`curl -H "Authorization: Bearer ACCESS_TOKEN" "https://stepic.org/api/social-accounts?provider=github&uid=1216"`

Response:

`{"meta": {"page": 1, "has_next": false, "has_previous": false}, "social-accounts": []}`

##### Authorization code flow

- Set `grant type = autorization_code` и `redirect_uri` inside aplication;
- Redirect user to  `https://stepic.org/oauth2/authorize/?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI;
`
- User should authenticate or register, and grant permissions to application.;
- User redirects to `redirect_uri` and sends `CODE`;
- Application asks for `ACCESS_TOKEN`: `curl -X POST -d "grant_type=authorization_code&code=CODE&redirect_uri=REDIRECT_URI" -u"CLIENT_ID:SECRET_ID" https://stepic.org/oauth2/token/`;
- Application behaves as user, adds `Authorization: Bearer ACCESS_TOKEN;` to every request
- Request to `https://stepic.org/api/stepics/1` returns current user.

##### Registration
Registration endpoint:

`POST /api/users`<br>
```{"user": {
  "first_name": "New",
  "last_name": "User",
  "email": "new.user@stepic.org",
  "password": "password",
}}```

For registering new user, current session should be not logged in (all non-logged users are `Guests`).<br>
You should obtain X-CSRFToken from session and use it with registration. Also HTTP request should include `referer` (eg `stepic.org`)

```
import random
import sys
import requests
import json
URL = 'https://stepic.org/accounts/signup/?next=/'
client = requests.session()
client.get(URL)
csrftoken = client.cookies['csrftoken']
user_email = str(random.randint(10000000, 100000000))+"@gmail.com"
login_data = dict(first_name=random.randint(10000000, 100000000), last_name=random.randint(10000000, 100000000),
                  email=user_email, password1='1337hax0r', password2='1337hax0r')
login_data['csrfmiddlewaretoken'] = csrftoken
login_data['next'] = '/'
response = client.post(URL, data=login_data, headers=dict(Referer=URL))
```
##### Multiple IDs
If needed, multiple objects can been asked by ID with one request. Here we asking for courses id = `2`, `67`, `76`, `70`<br>  
```
https://stepic.org/api/courses?ids[]=2&ids[]=67&ids[]=76&ids[]=70  …
```
Supported by all endpoins.


## Examples

###### Simple operations:<br>

- OAuth authorization example: <a href="/examples/oauth_auth_example.py">oauth_auth_example.py</a>


######Complete examples:<br>

- VideoDownloader: <a href="https://github.com/StepicOrg/stepic-oauth2-videodownloader">stepic-oauth2-videodownloader</a>

- iOS app: <a href="https://github.com/StepicOrg/stepic-ios">Stepic iOS app</a>

- Android app: <a href="https://github.com/StepicOrg/stepic-android">Stepic Android app</a>
