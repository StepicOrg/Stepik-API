import json
import requests
import numpy as np
import matplotlib.pyplot as plt


client_id = "mD7Vj1eRhl2i4xlz1jYqeG8d8LUGARgrqmd57Z9L"
client_secret = "zHXCSwWJNMKOIdpQg6RVTWDBPMJsBmIqXHrA1ISAgDr1p4MqV0325Unf2H" \
                "z8Z9DOIZDtQx8t533XCEwiRsgrhMEQOqJOiVEeGDbDGrT59H70asqCx6jW" \
                "6waPNqQ9WNJi"

auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth)
token = json.loads(resp.text)["access_token"]


def make_stepic_api_call_pk(name, pk, key):
    api_url = 'https://stepic.org/api/{}/{}'.format(name, pk)
    res = json.loads(
        requests.get(api_url,
                     headers={'Authorization': 'Bearer '+ token}).text
    )[name][0][key]
    return res


def get_all_steps_viewed_by(course):
    sections = make_stepic_api_call_pk("courses", course, "sections")
    units = [unit
             for section in sections
             for unit in
             make_stepic_api_call_pk("sections", section, "units")]
    assignments = [assignment
                   for unit in units
                   for assignment in
                   make_stepic_api_call_pk("units", unit, "assignments")]
    steps = [make_stepic_api_call_pk("assignments", assignment, "step")
             for assignment in assignments]
    viewed_by = [make_stepic_api_call_pk("steps", step, "viewed_by")
                 for step in steps]
    return viewed_by


def main():
    # This script gets view statistics for all of the steps in some course
    # and then displays it. The trend is usually (naturally) declining
    course = 187
    viewed_by = get_all_steps_viewed_by(course)
    plt.plot(np.array(viewed_by))
    plt.show()


if __name__ == '__main__':
    main()
