# client/style_engine/settings_mapper.py

import os
import requests
import json
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

def map_settings(scene_description: str, styles: list[str]) -> dict[str, dict]:
    """
    For each style in `styles`, calls Mistral to recommend:
      - ISO
      - Aperture
      - Shutter speed
      - White balance
      - One composition tip

    Returns a dict mapping style → settings dict.
    """
    results = {}
    for style in styles:
        system_prompt = (
            "You are a professional photographer with 20+ years of experience. "
            "Given a scene description and a desired mood/style, "
            "recommend ISO, aperture, shutter speed, white balance (Kelvin), "
            "and a single composition tip." \
            "in composition, try out all the unique composition techniques like golden ratio, fibbonachi spiral, leading lines etc" \
            "in the image, and recommend which of them is most suitable." \
        )
        user_prompt = (
            f"Scene: “{scene_description}”\n"
            f"Style: “{style}”\n\n"
            "Recommend:\n"
            "- ISO (integer)\n"
            "- aperture (e.g. f/2.8)\n"
            "- shutter (e.g. 1/60s)\n"
            "- white_balance (Kelvin)\n"
            "- one composition tip (text)\n\n"
            "Return a JSON object with keys: ISO, aperture, shutter, white_balance, tip."
        )
        payload = {
            "model": "open-mistral-7b",
            "temperature": 0.6, #controls randomness of model (0.3 made it stick very closely to what i said keep it 0.5 to 0.7)
            "messages": [
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_prompt}
            ]
        }

        resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        try:
            # Parse the JSON response into a dict
            settings = json.loads(content)
        except Exception:
            # In case the model didn't return strict JSON, do a quick fallback parser:
            import re
            def find_field(field):
                m = re.search(rf'"{field}"\s*:\s*("?[^",\n]+"?)', content)
                return m.group(1).strip('"') if m else None

            settings = {
                "ISO": int(find_field("ISO") or 100),
                "aperture": find_field("aperture") or "f/2.8",
                "shutter": find_field("shutter") or "1/60s",
                "white_balance": find_field("white_balance") or "5600K",
                "tip": find_field("tip") or ""
            }

        results[style] = settings

    return results
