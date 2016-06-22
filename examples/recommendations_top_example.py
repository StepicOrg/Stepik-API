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


def get_recommendation_reactions_lessons_count(pages_max_num=None):
    recommendation_reactions = get_api_requests('recommendation-reactions', pages_max_num)
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


def print_scores(top_lessons, titles=False):
    for lesson in top_lessons:
        lesson_id = lesson[0]
        num_recs = lesson[2] if titles else lesson[1]

        if titles:
            title = lesson[1]
            out_str = 'Course-ID: {0}, title: {1}, #recs: {2}'.format(lesson_id, title, num_recs)
        else:
            out_str = 'Course-ID: {0}, #recs: {1}'.format(lesson_id, num_recs)

        print(out_str)


if __name__ == "__main__":

    client_id = "..."
    client_secret = "..."

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    resp = requests.post('https://stepic.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth
                         )
    token = json.loads(resp.text)['access_token']

    lessons_top = get_recommendation_reactions_lessons_count(pages_max_num=50)

    lessons_top_10 = get_top_lessons(lessons_top, 10)

    print_scores(lessons_top_10)
