import requests


has_next = True
page = 0
titles = []
while has_next:
    page += 1
    url = 'https://stepic.org/api/courses?page={}'.format(page)
    courses = requests.get(url).json()['courses']
    has_next = requests.get(url).json()['meta']['has_next']

    page_titles = [course['title'] for course in courses]
    for title in page_titles:
        titles.append(title)

python_titles = 0
for title in titles:
    if 'python' in title.lower():
        python_titles += 1

if python_titles > len(titles) - python_titles:
    a = 'больше'
elif python_titles == len(titles) - python_titles:
    a = 'cтолько же'
else:
    a = 'меньше'

print('Курсов по Python {}.'.format(a))
