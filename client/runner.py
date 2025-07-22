# client/runner.py
#simple one shot runner for prototyping purpose, more robust runner with try catch and error handling in oldsource/runnerv2.py
import requests
import json
from dotenv import load_dotenv
import os

from mistral_client import call_mistral

load_dotenv() # Load .env file at the root

# Path to the image on your local machine
IMAGE_PATH = "/home/habanera/v2-engine/ashok_saravanan_ay_photography_11.jpg"  # actual image path

# Example structured intent parsed by Mistral (normally you'd get this from the intent parsing module)
structured_intent = {
    "mood": "melancholic",
    "subject": "woman by the window",
    "tone": "soft natural light",
    "focus": "emotional atmosphere"
}

# Convert intent to JSON string
intent_json = json.dumps(structured_intent)

# Define the FastAPI server endpoint
NGROK_URL = os.getenv("NGROK_URL") #Ngrok Kaggle webserver link 

if NGROK_URL is None:
    raise ValueError("NGROK_URL environment variable not set")

SERVER_URL = NGROK_URL + "/parse"
#don't hardcode urls,api keys always load them from env

# Prepare multipart/form-data request
files = {
    "image": open(IMAGE_PATH, "rb"),  # send image file
    "intent": (None, intent_json, "application/json")  # send intent as plain JSON
}

# Send POST request
try:
    response = requests.post(SERVER_URL, files=files)
    if response.status_code == 200:
        feedback = response.json().get("feedback", "No feedback returned.")
        print("\n Humanized Feedback:\n", feedback)
    else:
        print(f" Server error: {response.status_code}\n{response.text}")
except Exception as e:
    print(" Request failed:", e)


#prompt = "Give feedback on the photo quality and framing."
prompt = "You are a photography feedback assistant. Only respond based on provided image description and intent. If either is missing, say so clearly."
response = call_mistral(prompt)

print(" \n Mistral says:\n", response)
