import requests


def top_lessons_json(page):
    return requests.get("https://stepic.org:443/api/top-lessons?page={}".format(page)).json()


def top_lessons_indices():
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


def generate_html(top_lessons):
    html_container = []

    header = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=utf-8 />
        <title>Top lessons sorted by number of views</title>
    </head>
    """
    html_container.append(header)

    body = """
    <body>
    <table border = '1' align = 'center'>
        <tr>
            <th>Course title</th>
            <th>Viewed by</th>
            <th>Passed by</th>
        </tr>
    """
    html_container.append(body)

    lesson_template = """
        <tr>
            <td>{0}</td>
            <td>{1}</td>
            <td>{2}</td>
        </tr>
    """

    for lesson in top_lessons:
        html_container.append(lesson_template.format(*lesson))

    footer = """
    </table>
    </body>
    </html>
    """
    html_container.append(footer)

    return "".join(html_container)


def main():
    idxs = top_lessons_indices()

    top_lessons = []

    for idx in idxs:
        top_lessons.append(lesson_info(idx))

    top_lessons = sorted(top_lessons, key=lambda x: x[1], reverse=True)

    # Generate html and write it to file
    with open("top_lessons.html", "w+") as f:
        f.write(generate_html(top_lessons))

if __name__ == "__main__":
    main()
