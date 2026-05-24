import requests

INSTANCE_ID = "instance177209"  
TOKEN = "ue1g1m1yt1m3n5ns"
PHONE = "+918341282018"  # your full number

url = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"

payload = {
    "token": TOKEN,
    "to": PHONE,
    "body": "HELLO TEST 123"
}

response = requests.post(url, data=payload)
print("Status:", response.status_code)
print("Response:", response.json())