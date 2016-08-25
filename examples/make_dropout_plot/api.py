# Source: https://gist.github.com/vyahhi/0c639c7a17c4fc828cc0
# Updated with API functions

import json
import requests
from urllib.parse import urlencode

# 1. Get your keys at https://stepik.org/oauth2/applications/
# (client type = confidential, authorization grant type = client credentials)
# See: ./api_secret/api_secret_template.py
from .api_secret.api_secret_template import CLIENT_ID, CLIENT_SECRET

API_URL = 'https://stepik.org/api/{}'
API_HOST = 'https://stepik.org'


# 2. Get a token
def get_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepik.org/oauth2/token/', data={'grant_type': 'client_credentials'}, auth=auth)
    token = json.loads(resp.text)['access_token']
    return token


# 3. Call API (https://stepik.org/api/docs/) using this token.
def get_api_response(api_url, token=get_token()):
    response = requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).text

    try:
        response_json = json.loads(response)
    except json.decoder.JSONDecodeError:
        # if HTML, not JSON returned (e.g., pages with error 404 or 500)
        response_json = json.loads('{}')

    return response_json


# Additional API functions

def fetch_objects_by_id(object_name, object_id, token=get_token()):
    if type(object_id) is not list:
        # if it is a scalar, we create an one-element list
        object_id = [object_id]

    # Fetch objects by 30 items,
    # so we will not bump into HTTP request length limits
    slice_size = 30
    objects_from_api = []
    for i in range(0, len(object_id), slice_size):
        obj_ids_slice = object_id[i:i + slice_size]
        api_url = '{}/api/{}?{}'.format(
            API_HOST, object_name, '&'.join('ids[]={}'.format(obj_id) for obj_id in obj_ids_slice))
        response = requests.get(api_url,
                                headers={'Authorization': 'Bearer ' + token}
                                ).json()
        objects_from_api += response[object_name]
    return objects_from_api


def fetch_objects_by_pk(object_name, object_pk, token=get_token()):
    api_url = '{}/api/{}/{}'.format(API_HOST, object_name, object_pk)
    response = get_api_response(api_url, token)
    objects_from_api = response[object_name]
    return objects_from_api


def fetch_objects(object_name, token=get_token(), **kwargs):
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
            if 'meta' not in response:
                # if not success (e.g., error 404), then return collected objects
                return objects_from_api

            objects_from_api += response[object_name]
            has_next = response['meta']['has_next']
            if not has_next:
                break
            params['page'] += 1

    return objects_from_api
