import requests


def generate_html(top_lessons):
    rows = ""

    for lesson in top_lessons:
        rows += """<tr>
            <td><a href="https://stepik.org/lesson/{id}">{title}</a></td>
            <td>{viewed_by}</td>
            <td>{passed_by}</td>
            <td>{vote_delta}</td>
        </tr>""".format(**lesson)

    template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset=utf-8 />
            <title>Top lessons sorted by number of views</title>
        </head>
        <body>
        <table border="1" align="center">
            <tr>
                <th>Course title</th>
                <th>Viewed by</th>
                <th>Passed by</th>
                <th>Vote delta</th>
            </tr>
            {rows}
        </table>
        </body>
        </html>
    """

    return template


def main():
    # To sort by votes we use "order" query parameter
    top_lessons = requests.get("https://stepik.org:443/api/lessons?order=-vote_delta").json()["lessons"]

    # Sort by number of views
    lessons = sorted(top_lessons, key=lambda x: x["viewed_by"], reverse=True)

    # Generate html and write it to file
    with open("top_lessons.html", "w+") as f:
        f.write(generate_html(lessons))


if __name__ == "__main__":
    main()
