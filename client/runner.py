# client/runner.py

import os
import json
import requests
from dotenv import load_dotenv

from style_engine.style_suggestor import suggest_styles
from style_engine.settings_mapper import map_settings


load_dotenv()

# ——————————————————————————————————————————
# 1) Configuration
# ——————————————————————————————————————————

IMAGE_PATH = "/home/habanera/v2-engine/ashok_saravanan_ay_photography_11.jpg"  # ← replace with your real local image path

# Toggle this to True if you want Route 2 (comparative mode)
USE_INTENT = False

# If USE_INTENT=True, define your structured intent here:
structured_intent = {
    "mood":    "Reflective",
    "subject": "child in colors",
    "tone":    "vibrant colors",
    "focus":   "emotional atmosphere"
}
intent_json = json.dumps(structured_intent) if USE_INTENT else None

# Read your Ngrok‑exposed FastAPI base URL
NGROK_URL = os.getenv("NGROK_URL") 
if not NGROK_URL:
    raise EnvironmentError("NGROK_URL not set in .env")

# Endpoints
DESCRIBE_URL = NGROK_URL.rstrip("/") + "/describe"
PARSE_URL    = NGROK_URL.rstrip("/") + "/parse"

# ——————————————————————————————————————————
# 2) Runner logic
# ——————————————————————————————————————————

try:
    if not USE_INTENT:
        # — Route 1: Suggestion Engine (Scene description only) —
        print(" Running Route 1 (no intent)…\n")

        with open(IMAGE_PATH, "rb") as img_f:
            resp = requests.post(DESCRIBE_URL, files={"image": img_f}, timeout=30)
            resp.raise_for_status()

        scene_description = resp.json().get("image_description")
        if not scene_description:
            raise RuntimeError("No scene description returned: " + resp.text)

        print(" Scene description (Route 1):\n")
        print(scene_description)

        # ← Here is where you’ll later call your style_suggester() and map_settings()
        styles = suggest_styles(scene_description, top_k=3) #style_suggestor plugged in
        print("Suggested styles:\n", styles, "\n")

        settings_per_style = map_settings(scene_description, styles) # Map each style to concrete camera settings
        print("Mapped settings per style:\n", json.dumps(settings_per_style, indent=2), "\n")

        #print("Styles:", styles, "Settings:", settings)

    else:
        # — Route 2: Comparative Feedback (image + intent) —
        print(" Running Route 2 (with intent)…\n")

        with open(IMAGE_PATH, "rb") as img_f:
            files = {"image": img_f}
            data  = {"intent": intent_json}
            resp = requests.post(PARSE_URL, files=files, data=data, timeout=30)
            resp.raise_for_status()

        payload = resp.json()
        image_desc = payload.get("image_description", "—")
        intent_echo = payload.get("intent_text", "—")
        print(" LLaVA saw:\n", image_desc, "\n")
        print(" Intent was:\n", intent_echo, "\n")

        # ← And here you can later wrap in additional comparison or humanization:
        #    feedback = generate_comparative_feedback(payload)
        #    print("Feedback:\n", feedback)

except Exception as e:
    print(" Runner failed:", repr(e))
