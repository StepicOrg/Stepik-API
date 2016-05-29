import requests


def top_lessons_json(page):
    return requests.get("https://stepic.org:443/api/top-lessons?page={}".format(page)).json()


def top_lessons_indexes():
    idxs = []
    cur_page = 1

    while True:
        r = top_lessons_json(cur_page)

        for top_lesson in r["top-lessons"]:
            idxs.append(top_lesson["lesson"])

        if not r["meta"]["has_next"]:
            break

        cur_page += 1

    return idxs


def lesson_info(idx):
    r = requests.get("https://stepic.org:443/api/lessons/{}".format(idx)).json()
    lesson = r["lessons"][0]

    return lesson["title"], lesson["viewed_by"], lesson["passed_by"]


def main():
    print("Top lessons sorted by number of views")
    print("Format: (Title, Viewed by, Passed by)")
    idxs = top_lessons_indexes()

    top_lessons = []

    for idx in idxs:
        top_lessons.append(lesson_info(idx))


    top_lessons = sorted(top_lessons, key=lambda x: x[1], reverse = True)

    for lesson in top_lessons:
        print(lesson)


if __name__ == "__main__":
    main()
