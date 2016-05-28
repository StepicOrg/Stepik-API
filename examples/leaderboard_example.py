import requests

r = requests.get("https://stepic.org/api/leaders")

print "Current leaders:\n"

for leader in r.json()["leaders"]:
    user = requests.get("https://stepic.org/api/users/" + str(leader["user"])).json()["users"][0]
    print leader["score"], '\t', user['first_name'], user['last_name']