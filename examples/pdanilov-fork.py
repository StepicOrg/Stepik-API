import sys
import json
import requests
from collections import Counter


def get_request(url):
    return json.loads(requests.get(url, headers={'Authorization': 'Bearer '+ token}).text)


def get_recommendation_reactions_lessons_count():
    recommend_reacs_lessons = []
    page_num = 1

    while True:
        recommend_reacs_data = get_request('https://stepic.org/api/recommendation-reactions?page={}'.format(page_num))
        recommend_reacs = recommend_reacs_data['recommendation-reactions']

        for rec in recommend_reacs:
            recommend_reacs_lessons.append(rec['lesson'])

        if not recommend_reacs_data['meta']['has_next']:
            break
        else:
            page_num += 1

    return Counter(recommend_reacs_lessons)


def get_top_lesson_titles(top_ids, n):
    top_lesson_titles_dict = {}
    lessons_list = []
    page_num = 1

    while True:
        lessons_data = get_request('https://stepic.org/api/lessons?page={}'.format(page_num))
        lessons = lessons_data['lessons']

        for lesson in lessons:
            lessons_list.append(lesson)

        if not lessons_data['meta']['has_next']:
            break
        else:
            page_num += 1

    top_n_ids = [top_ids[idx] for idx in range(n)]

    for id in top_n_ids:

        for lesson in lessons_list:

            if lesson['id'] == id:
                top_lesson_titles_dict[id] = lesson['title']

    return top_lesson_titles_dict


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: script_name.py client_id client_secret")
        exit()

    client_id = sys.argv[1]
    client_secret = sys.argv[2]

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepic.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth
                         )
    token = json.loads(resp.text)['access_token']

    lessons_top = get_recommendation_reactions_lessons_count()

    sorted_keys = [key for (key, value) in sorted(lessons_top.items(), key=lambda x: x[1], reverse=True)]
    top_lesson_titles = get_top_lesson_titles(sorted_keys, 10)

    for lesson_top_id in top_lesson_titles.keys():
        print('ID: {0}, title: {1}, #recs: {2}'
              .format(lesson_top_id, top_lesson_titles[lesson_top_id], lessons_top[lesson_top_id]))
