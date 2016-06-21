import json
import requests


def get_token():
    client_id = "n4mnzQGfDEfOhFixwBvLV2mZJJLvf86pzfMMiPF5"
    client_secret = "40ON9IPJRDAngUkVbGBTEjCBAwc2wB7lV8e71jJUPKabdKq6KBTUBKb1xGkh82KtAI1AqISrL" \
                    "3Zi4sTfhCBVh27YvlV6Y5klpXXV5loUWvuhMSRiN3HRZzVDO0fLBibv"

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepic.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth)
    token = json.loads(resp.text)['access_token']
    return token


def get_data(pageNum):
    api_url = 'https://stepic.org/api/courses?page={}'.format(pageNum)
    course = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + get_token()}).text)
    return course


def get_chosen_courses(amountOfUnits, courseLang, amountOfDiscuss):
    pageNum = 0
    hasNextPage = True
    listOfChoices = []
    while hasNextPage:
        try:
            pageNum += 1
            pageContent = get_data(pageNum)
            hasNextPage = pageContent['meta']['has_next']
            courses = pageContent['courses']
            for course in courses:  # Select only active courses (courses with active session)
                if ((course['total_units']) > amountOfUnits and (course['language'] == courseLang)
                    and (course['is_active'] == True) and (course['discussions_count'] > amountOfDiscuss)):
                    listOfChoices.append({
                        'course_name': course['slug'],
                        'amount_of_units': course['total_units'],
                        'language': course['language'],
                        'create_date': course['create_date'],
                        'discussions_count': course['discussions_count']
                    })
        except:
            print("Error exception: something was broken!")

    print(listOfChoices)


def main():
    # Choose values of parameters for a course choice
    # Example:
    amountOfUnits = 5  # amount of units in a course
    courseLang = 'ru'  # language of the chosen course
    amountOfDiscuss = 30  # number of discussions in a course (as an indicator of the popularity)
    get_chosen_courses(amountOfUnits, courseLang, amountOfDiscuss)

main()
