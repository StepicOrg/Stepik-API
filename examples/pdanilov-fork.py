import sys
import json
import requests
from collections import Counter


api_url = 'https://stepic.org/api/'


def get_api_requests(topic, pages_max_num=None):
    result = []
    page_num = 1

    while True if pages_max_num is None else page_num <= pages_max_num:
        request_url = (api_url + topic + '?page={}').format(page_num)
        request_data = json.loads(requests.get(request_url, headers={'Authorization': 'Bearer '+ token}).text)
        request_result = request_data[topic]
        result.extend(request_result)

        if not request_data['meta']['has_next']:
            break
        else:
            page_num += 1

    return result


def get_recommendation_reactions_lessons_count():
    recommendation_reactions = get_api_requests('recommendation-reactions')
    recommendation_reactions_lessons = [item['lesson'] for item in recommendation_reactions]
    return Counter(recommendation_reactions_lessons)


def get_top_lessons(recommendations, n, titles=False):
    sorted_keys = [key for (key, value) in sorted(lessons_top.items(), key=lambda x: x[1], reverse=True)]

    top_n_keys = sorted_keys[:n]

    if titles:
        lessons = get_api_requests('lessons')
        top_lessons_list = []

        for id in top_n_keys:

            for lesson in lessons:

                if lesson['id'] == id:
                    top_lessons_list.append((id, lesson['title'], recommendations[id]))
                    break

    else:
        top_lessons_list = [(id, recommendations[id]) for id in top_n_keys]

    return top_lessons_list


if __name__ == "__main__":

    assert(len(sys.argv) == 3, "Usage: script_name.py client_id client_secret")

    client_id = sys.argv[1]
    client_secret = sys.argv[2]

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepic.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth
                         )
    token = json.loads(resp.text)['access_token']

    lessons_top = get_recommendation_reactions_lessons_count()

    top_lesson_titles = get_top_lessons(lessons_top, 10, titles=True)

    for lesson_id, title, num_recs in top_lesson_titles:
        print('ID: {0}, title: {1}, #recs: {2}'.format(lesson_id, title, num_recs))
