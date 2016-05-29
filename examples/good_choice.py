import json
import requests

client_id = "n4mnzQGfDEfOhFixwBvLV2mZJJLvf86pzfMMiPF5"
client_secret = "40ON9IPJRDAngUkVbGBTEjCBAwc2wB7lV8e71jJUPKabdKq6KBTUBKb1xGkh82KtAI1AqISrL" \
                "3Zi4sTfhCBVh27YvlV6Y5klpXXV5loUWvuhMSRiN3HRZzVDO0fLBibv"

auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
resp = requests.post('https://stepic.org/oauth2/token/',
                     data={'grant_type': 'client_credentials'},
                     auth=auth
                     )
token = json.loads(resp.text)['access_token']

def get_data(page_num):
    api_url = 'https://stepic.org/api/courses?page={}'.format(page_num)
    course = json.loads(requests.get(api_url, headers={'Authorization': 'Bearer ' + token}).text)
    return course

def get_chosen_courses():
    has_next_page = True
    page_num = 0
    list_of_choices = []
    while has_next_page:
        try:
            page_num += 1
            page_content = get_data(page_num)
            has_next_page = page_content['meta']['has_next']
            courses = page_content['courses']
            for course in courses:
                if ((course['total_units']) > 5 and (course['language'] == 'ru')
                    and (course['is_active'] == True) and (course['discussions_count'] > 30)):
                    list_of_choices.append({
                        'course_name': course['slug'],
                        'amount_of_units': course['total_units'],
                        'language': course['language'],
                        'create_date': course['create_date'],
                        'discussions_count': course['discussions_count']
                    })
        except:
            print ("Error exception: something was broken!")

    print (list_of_choices)

def main():
    get_chosen_courses()

if __name__ == '__main__':
    main()
