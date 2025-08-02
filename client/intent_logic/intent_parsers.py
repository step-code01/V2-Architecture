import requests
import json
import re

import os, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY  = os.getenv("MISTRAL_API_KEY")
API_URL  = "https://api.mistral.ai/v1/chat/completions"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def parse_intent(free_text: str) -> tuple[dict, float]:
    system = (
        "You are an expert with 20+ years of experience at parsing photographic intent into JSON keys "
        "mood, subject, tone, focus, and all 360 degree aspects of photography. "
        "Analyse the user's prompt trying to understand what they are trying to achieve with the photo they want to click. "
        "Examples: If they are unsure by saying things like 'I don't know what I want', or if they say 'I don't know why this looks good', "
        "analyse accordingly and give insight. Your job is to interpret uncertain or exploratory prompts and convert them into structured JSON."
    )

    user = f"Convert this into a single JSON object with keys mood, subject, tone, focus, and include a confidence score between 0 and 1:\n\n\"{free_text}\""

    payload = {
        "model": "open-mistral-7b",
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    }

    resp = requests.post(API_URL, json=payload, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()["choices"][0]["message"]["content"]

    # STEP 1: Extract all JSON-like objects from the string using regex
    potential_jsons = re.findall(r'\{.*?\}', data, re.DOTALL)

    for chunk in potential_jsons:
        try:
            parsed = json.loads(chunk)
            # Check if required keys are present
            if all(k in parsed for k in ("mood", "subject", "tone", "focus")):
                confidence = parsed.pop("confidence", 0.5)
                return parsed, confidence
        except json.JSONDecodeError as e:
            print(f"[WARN] Skipping invalid JSON block: {e}")
            continue

    # If no valid JSON found
    print("[ERROR] No valid JSON intent found.")
    return {}, 0.0
