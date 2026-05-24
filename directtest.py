import requests

INSTANCE_ID = "instance177209"
TOKEN = "ue1g1m1yt1m3n5ns"

result = requests.post(
    f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat",
    data={
        "token": TOKEN,
        "to": "+918341282018",
        "body": "TEST MESSAGE from StudyMind AI"
    }
).json()

print(result)