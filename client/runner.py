# client/runner.py
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

IMAGE_PATH = "/home/habanera/v2-engine/ashok_saravanan_ay_photography_11.jpg"   #actual image path

structured_intent = {
    "mood": "Reflective",
    "subject": "child in colors",
    "tone": "vibrant colors",
    "focus": "emotional atmosphere"
}
intent_json = json.dumps(structured_intent)

NGROK_URL = os.getenv("NGROK_URL")
if NGROK_URL is None:
    raise ValueError("NGROK_URL environment variable not set")

SERVER_URL = NGROK_URL.rstrip("/") + "/parse"

files = {
    "image": open(IMAGE_PATH, "rb"),
}
data = {
    "intent": intent_json
}

try:
    print("Sending request to:", SERVER_URL)
    response = requests.post(SERVER_URL, files=files, data=data)
    print("Status code:", response.status_code)
    #print("Response body:", response.text)

    if response.status_code == 200:
        parsed_desc = response.json().get("image_description","No image description returned.")
        print("Parsed image:", parsed_desc)
    else:
        print(f"Server error {response.status_code}: {response.text}")
except Exception as e:
    print("Request failed:", repr(e))
