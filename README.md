# Stepic.org API Readme

Stepic.org has REST API in JSON format. API endpoints are listed on https://stepic.org/api/docs, and you can also make API call there (but this page is limited to `GET` requests). 

Stepic.org use the same API for its web front-end (JS app) and its iOS/Android applications. Therefore, almost all the platform features are supported in this API.

All API examples are up to date and working if the build status is `passed`: [![Build Status](https://travis-ci.org/StepicOrg/stepic-api-docs.svg?branch=master)](https://travis-ci.org/StepicOrg/stepic-api-docs) 

## Flat

Stepic API schema is flat, i.e. there are no nested end-points.

Every request returns a list of objects, even if only one object was requested. This list can contain 0 or more elements.

For example: `https://stepic.org/api/courses/1` returns not a single course, but a list with single course.

## Pagination

All responses from `GET` requests are paginated. They contain extra `meta` object with the information about pagination. It may looks like this:
```
{
    meta: {
        page: 1,
        has_next: true,
        has_previous: false
    },
    requested_objects: [...]
}
```

If the next page exists, then it can be requested using get parameter `?page=...`. By default, if no parameter is given, it's equal to 1.

For example: `https://stepic.org/api/courses` is equal to `https://stepic.org/api/courses?page=1`. Next page: `https://stepic.org/api/courses?page=2` and so on.

Usual page size is equal to 20 elements, but it can vary due to API endpoint, users permissions etc. We <b>do not recommend to rely on a constant page size</b>.

## Side-Loading

Response may also contain multiple objects, related to the requested object. 

For example: for registered user, response from `https://stepic.org/api/courses` also includes user's course `enrollments`. 

## OAuth 2

In order to call Stepic.org API as a registered uses, you can use this user's OAuth2 keys.
You can get your keys by creating an application on https://stepic.org/oauth2/applications/ (while being logged in), and you can also set `redirect_uri`, `Client type` and `Authorization grant type` there.

Authorization endpoint (Authorization code, Implicit grant; redirect_uri needed): `https://stepic.org/oauth2/authorize/.`

Token endpoint (Authorization code, Password и Client credentials): `https://stepic.org/oauth2/token/`.

#### Client credentials flow

You can than obtain access token using the following client credential flow:

`curl -X POST -d "grant_type=client_credentials" -u"CLIENT_ID:CLIENT_SECRET" https://stepic.org/oauth2/token/`<br>

Response: 

`{"access_token": "ACCESS_TOKEN", "scope": "read write", "expires_in": 36000, "token_type": "Bearer"}`

Example with access token:

`curl -H "Authorization: Bearer ACCESS_TOKEN" "https://stepic.org/api/social-accounts?provider=github&uid=1216"`

Response:

`{"meta": {"page": 1, "has_next": false, "has_previous": false}, "social-accounts": []}`

#### Authorization code flow

- Set `grant type = autorization_code` and set `redirect_uri` in your aplication;
- Redirect user to `https://stepic.org/oauth2/authorize/?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI`;
- User should authenticate or register, and grant permissions to application;
- It redirects to `redirect_uri` and receives the `CODE`;
- Application asks for `ACCESS_TOKEN`: `curl -X POST -d "grant_type=authorization_code&code=CODE&redirect_uri=REDIRECT_URI" -u"CLIENT_ID:SECRET_ID" https://stepic.org/oauth2/token/`;
- Application behaves as user, adding `Authorization: Bearer ACCESS_TOKEN;` to request headers.
- Request to `https://stepic.org/api/stepics/1` returns the current user.

## Registration

Registration endpoint:

`POST /api/users`

```
{"user": {
  "first_name": "New",
  "last_name": "User",
  "email": "new.user@stepic.org",
  "password": "password",
}}
```

For registering a new user, current session should belong to a guest (non-logged user). I.e. you should get X-CSRFToken from the session (e.g. open stepic.org and take it from headers) and pass it back during the registration (in request headers). 
Also HTTP request should include `referer` (e.g. `stepic.org`).

Example:
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

## Multiple IDs Calls

You can request multiple objects using the single API call by using `?ids[]=2&ids[]=3...`.

For example: to get courses with IDs = `2`, `67`, `76` and `70`; you can to call `https://stepic.org/api/courses?ids[]=2&ids[]=67&ids[]=76&ids[]=70`.

This syntax is supported by all API endpoints.

Don't make calls with large number of ids[0]. Such calls may be rejected by the server because of a large HTTP header.

## Examples

#### Simple operations:

- OAuth authorization example: [oauth_auth_example.py](/examples/oauth_auth_example.py)

#### Complete examples:

* VideoDownloader: [stepic-oauth2-videodownloader](https://github.com/StepicOrg/stepic-oauth2-videodownloader)
* iOS app: [Stepic iOS app](https://github.com/StepicOrg/stepic-ios)
* Android app: [Stepic Android app](https://github.com/StepicOrg/stepic-android)
* Code Challenge submitter: [submitter.py](https://github.com/StepicOrg/SubmissionUtility/blob/master/submitter.py)
* Video uploading (C#): [CoursePublishing](https://github.com/okulovsky/CoursePublishing/tree/master/Publishing/Stepic)
