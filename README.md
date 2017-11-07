# Stepik.org API Readme

Stepik.org has REST API in JSON format. API endpoints are listed on https://stepik.org/api/docs, and you can also make API call there (but this page is limited to `GET` requests).

Stepik.org use the same API for its web front-end (JS app) and its iOS/Android applications. Therefore, almost all the platform features are supported in this API.

All API examples are up to date and working if the build status is `passing`: [![Build Status](https://travis-ci.org/StepicOrg/Stepik-API.svg?branch=master)](https://travis-ci.org/StepicOrg/Stepik-API)

## Flat

Stepik API schema is flat, i.e. there are no nested end-points.

Every request returns a list of objects, even if only one object was requested. This list can contain 0 or more elements.

For example: `https://stepik.org/api/courses/1` returns not a single course, but a list with single course.

## Pagination

All responses to `GET` requests are paginated. They contain extra `meta` object with the information about pagination. It may look like this:
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

If the next page exists, then it can be requested using get parameter `?page=...`. By default, if no parameter is given, it’s equal to 1.

For example: `https://stepik.org/api/courses` is equal to `https://stepik.org/api/courses?page=1`. Next page: `https://stepik.org/api/courses?page=2` and so on.

Usual page size is equal to 20 elements, but it can vary due to API endpoint, user’s permissions etc. We <b>do not recommend to rely on a constant page size</b>.

## Side-Loading

Response may also contain multiple objects, related to the requested object.

For example: for registered user, response from `https://stepik.org/api/courses` also includes user’s course `enrollments`.

## OAuth 2

In order to call Stepik.org API as a registered user, you can use this user’s OAuth2 keys.
You can get your keys by creating an application on https://stepik.org/oauth2/applications/ (while being logged in), and you can also set `redirect_uri`, `Client type` and `Authorization grant type` there.

Authorization endpoint (Authorization code, Implicit grant; redirect_uri needed): `https://stepik.org/oauth2/authorize/.`

Token endpoint (Authorization code, Password and Client credentials): `https://stepik.org/oauth2/token/`.

#### Client credentials flow

You can then obtain access token using the following client credential flow:

`curl -X POST -d "grant_type=client_credentials" -u"CLIENT_ID:CLIENT_SECRET" https://stepik.org/oauth2/token/`

Response:

`{"access_token": "ACCESS_TOKEN", "scope": "read write", "expires_in": 36000, "token_type": "Bearer"}`

Example with access token:

`curl -H "Authorization: Bearer ACCESS_TOKEN" "https://stepik.org/api/social-accounts?provider=github&uid=1216"`

Response:

`{"meta": {"page": 1, "has_next": false, "has_previous": false}, "social-accounts": []}`

#### Authorization code flow

- Set `grant type = autorization_code` and set `redirect_uri` in your application;
- Redirect user to `https://stepik.org/oauth2/authorize/?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI`;
- User should authenticate or register, and grant permissions to application;
- It redirects to `redirect_uri` and receives the `CODE`;
- Application asks for `ACCESS_TOKEN`: `curl -X POST -d "grant_type=authorization_code&code=CODE&redirect_uri=REDIRECT_URI" -u"CLIENT_ID:SECRET_ID" https://stepik.org/oauth2/token/`;
- Application behaves as user, adding `Authorization: Bearer ACCESS_TOKEN;` to request headers.
- Request to `https://stepik.org/api/stepics/1` returns the current user.

## Multiple IDs Calls

You can request multiple objects using the single API call by using `?ids[]=2&ids[]=3...`.

For example: to get courses with IDs = `2`, `67`, `76` and `70`; you can to call `https://stepik.org/api/courses?ids[]=2&ids[]=67&ids[]=76&ids[]=70`.

This syntax is supported by all API endpoints.

Don’t make calls with large size of `ids[]`. Such calls may be rejected by the server because of a large HTTP header.

## Examples

#### Simple operations:

- OAuth authorization example: [oauth_auth_example.py](/examples/oauth_auth_example.py)

#### Complete examples:

* VideoDownloader: [stepik-oauth2-videodownloader](https://github.com/StepicOrg/stepic-oauth2-videodownloader)
* iOS app: [Stepik iOS app](https://github.com/StepicOrg/stepic-ios)
* Android app: [Stepik Android app](https://github.com/StepicOrg/stepic-android)
* Code Challenge submitter: [submitter.py](https://github.com/StepicOrg/SubmissionUtility/blob/master/submitter.py)
* Video uploading (C#): [CoursePublishing](https://github.com/okulovsky/CoursePublishing/tree/master/Publishing/Stepic)
* PyCharm Edu & IntelliJ integration: [intellij-community](https://github.com/JetBrains/intellij-community/tree/7e16c042a19767d5f548c84f88cc5edd5f9d1721/python/educational-core/student/src/com/jetbrains/edu/learning/stepic)
* IntelliJ Plugin for Code Challenges: [intellij-plugins](https://github.com/StepicOrg/intellij-plugins)
