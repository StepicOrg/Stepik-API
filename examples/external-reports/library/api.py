import json
import requests

from urllib.parse import urlencode

# 1. Get your keys at https://stepik.org/oauth2/applications/
# (client type = confidential, authorization grant type = client credentials)
# and write them to api_keys.py
from api_keys import API_HOST, CLIENT_ID, CLIENT_SECRET


# 2. Get a token
def get_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    response = requests.post('{}/oauth2/token/'.format(API_HOST), data={'grant_type': 'client_credentials'}, auth=auth)
    # status code should be 200 (HTTP OK)
    assert(response.status_code == 200)
    token = json.loads(response.text)['access_token']
    return token


# 3. Call API ({API_HOST}/api/docs/) using this token.
def get_api_response(api_url, token=None):
    if not token:
        token = get_token()
    response = requests.get(api_url, headers={'Authorization': 'Bearer ' + token})
    # status code should be 200 (HTTP OK)
    assert (response.status_code == 200)

    return response.json()


# Additional API functions

def fetch_objects_by_id(object_name, object_id, token=None):
    if not token:
        token = get_token()

    if type(object_id) is not list:
        # if it is not a list, we create an one-element list
        object_id = [object_id]

    # Fetch objects by 30 items,
    # so we will not bump into HTTP request length limits
    slice_size = 30
    objects_from_api = []
    for i in range(0, len(object_id), slice_size):
        obj_ids_slice = object_id[i:i + slice_size]
        api_url = '{}/api/{}?{}'.format(
            API_HOST, object_name, '&'.join('ids[]={}'.format(obj_id) for obj_id in obj_ids_slice))
        response = get_api_response(api_url, token)
        objects_from_api += response[object_name]
    return objects_from_api


def fetch_objects_by_pk(object_name, object_pk, token=None):
    if not token:
        token = get_token()

    api_url = '{}/api/{}/{}'.format(API_HOST, object_name, object_pk)
    response = get_api_response(api_url, token)
    objects_from_api = response[object_name]
    return objects_from_api


def fetch_objects(object_name, token=None, **kwargs):
    if not token:
        token = get_token()

    if 'pk' in kwargs:
        # fetch objects by pk
        return fetch_objects_by_pk(object_name, kwargs['pk'], token)
    elif 'id' in kwargs:
        # fetch objects by ids
        return fetch_objects_by_id(object_name, kwargs['id'], token)
    else:
        # fetch objects by other params
        params = kwargs

        # can be pagination
        if 'page' not in kwargs:
            params = dict(params, page=1)

        objects_from_api = []
        while True:
            query = urlencode(params, doseq=True)
            api_url = '{}/api/{}?{}'.format(API_HOST, object_name, query)

            response = get_api_response(api_url, token)
            if object_name not in response:
                # if not success (e.g., error 404), then return collected objects
                return objects_from_api

            objects_from_api += response[object_name]
            has_next = response['meta']['has_next']
            if not has_next:
                break
            params['page'] += 1

        return objects_from_api


def create_object(object_name, data,  token=None):
    if not token:
        token = get_token()

    api_url = '{}/api/{}'.format(API_HOST, object_name)
    # use POST to create new objects
    response = requests.post(api_url, headers={'Authorization': 'Bearer ' + token}, json=data)
    # status code should be 201 (HTTP Created)
    assert(response.status_code == 201)
    object_id = response.json()[object_name][0]['id']
    return object_id


def update_object(object_name, object_id, data, token=None):
    if not token:
        token = get_token()

    api_url = '{}/api/{}/{}'.format(API_HOST, object_name, object_id)
    # use PUT to update existing objects
    response = requests.put(api_url, headers={'Authorization': 'Bearer ' + token}, json=data)
    # status code should be 200 (HTTP OK)
    assert(response.status_code == 200)
    object_id = response.json()[object_name][0]['id']
    return object_id
