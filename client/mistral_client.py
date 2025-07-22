import os
import requests
from dotenv import load_dotenv

#Step -1: Load variables from .env
load_dotenv()

#Step -2: Get the API key
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Step 3: Ensure key is present
if not MISTRAL_API_KEY:
    raise EnvironmentError(" Missing MISTRAL_API_KEY in .env file.")

# Step 4: Use the key in your API call
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

#calling mistral
def call_mistral(prompt: str, model: str = "open-mistral-7b") -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    if MISTRAL_API_URL is None:
        raise ValueError("MISTRAL_API_URL environment variable not set")
    
    response = requests.post(MISTRAL_API_URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise RuntimeError(f" Mistral API error: {response.status_code} - {response.text}")











































'''
def get_feedback(intent, llava_output):
    prompt = f"""
You are a photography mentor. The user has shared the following **intent** and a parsed image description.

Intent:
{intent}

Image Analysis:
{llava_output}

Please evaluate how well the image aligns with the intent and offer useful, friendly feedback on what works and what could improve.
"""

    payload = {
        "model": "mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(MISTRAL_API_URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Failed: {response.status_code} - {response.text}")'''




'''Make sure to keep Mistral API key:
In a .env file and load via os.getenv()
Or securely stored using key vaults if deploying

DO NOT FKING COMMIT YOUR KEYS TO GITHUB! SAME FOR KAGGLE!'''














'''
prompt structure
You are a photography mentor. The user has shared the following **intent** and a parsed image description.

Intent:
"moody night street with emotional distance"

Image Analysis:
- The photo is taken at night with ambient light from distant street lamps.
- A lone figure is walking away in the background.
- High contrast shadows obscure parts of the frame.
- Colors are muted, with blue-orange tones.

Please evaluate how well the image aligns with the intent and offer useful, friendly feedback on what works and what could improve.
'''

