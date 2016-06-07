import requests
import grequests

r = requests.get("https://stepic.org/api/leaders")  # get the first page of leader list

leaders = ["https://stepic.org/api/users/" + str(leader["user"])
           for leader in r.json()["leaders"]]  # form urls for leaders

scores = {l["user"]: l["score"] for l in r.json()["leaders"]}  # remember all scores

rs = [grequests.get(l) for l in leaders]  # prepare all requests
result = grequests.map(rs)  # execute requests concurrently

print("Current leaders:\n")

for r in result:
    user = r.json()["users"][0]
    print(scores[user["profile"]], '\t', user['first_name'], user['last_name'])