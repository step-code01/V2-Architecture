# client/style_engine/style_suggester.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.mistral.ai/v1/chat/completions"
API_KEY = os.getenv("MISTRAL_API_KEY")
if not API_KEY:
    raise EnvironmentError("MISTRAL_API_KEY not set in .env")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def suggest_styles(scene_description: str, top_k: int = 3) -> list[str]:
    system_prompt = (
        "You are a creative photography stylist. "
        "Given a scene description, suggest distinct moods or styles "
        "that would suit that scene. Return exactly the number of styles requested, "
        "each as a short phrase." \
        "Give something that is actually useful and works. "
    )
    user_prompt = (
        f"Scene: “{scene_description}”\n\n"
        f"Suggest {top_k} photographic moods/styles, each in one phrase."
    )

    payload = {
        "model": "open-mistral-7b",
        "temperature": 0.8,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as http_err:
        # Print out the entire response body for debugging
        print("Mistral API error:", http_err)
        print("Response status:", resp.status_code)
        print("Response body:", resp.text)
        # Reraise or return a safe fallback
        raise

    data = resp.json()
    text = data["choices"][0]["message"]["content"]

    # Parse into a list of style phrases
    lines = [line.strip("-•0123456789. )") for line in text.splitlines() if line.strip()]
    return lines[:top_k]
