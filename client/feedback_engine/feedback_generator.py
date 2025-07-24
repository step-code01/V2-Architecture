# client/feedback_engine/feedback_generator.py

import os
import requests
from dotenv import load_dotenv
import json
from typing import Optional

load_dotenv()

API_URL = "https://api.mistral.ai/v1/chat/completions"
API_KEY = os.getenv("MISTRAL_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_feedback(scene: str, styles: list[str], settings: dict[str, dict], composition_flags:  Optional[list[str]] = None) -> str:
    #route 1 feedback engine
    """
    Takes scene description, style list, per‑style settings, and optional composition flags,
    and returns a single mentor‑style advice string.
    """
    flags = composition_flags or []
    # Build a system prompt that sets your tone/role
    system_prompt = (
        "You are Throughline, a friendly photography mentor. "
        "You help photographers bridge the gap between their creative vision and their final image. "
        "Given scene context, creative styles, and technical settings, provide a concise piece of advice "
        "that highlights one style and explains how to execute it well."
    )

    # Build a user prompt that lays out everything
    user_prompt = f"Scene: {scene}\n\n"
    if flags:
        user_prompt += "Composition notes: " + "; ".join(flags) + "\n\n"
    user_prompt += "Styles and settings:\n"
    for style in styles:
        s = settings[style]
        user_prompt += (
            f"- {style}: ISO {s['ISO']}, {s['aperture']}, {s['shutter']}, WB {s['white_balance']}. Tip: {s['tip']}\n"
        )
    user_prompt += "\nPlease respond with **one** clear paragraph that picks the best style and tells the user how to achieve it, "
    user_prompt += "mentioning the key settings and any composition tip."

    payload = {
        "model": "open-mistral-7b",
        "temperature": 0.5,
        "messages": [
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_prompt}
        ]
    }

    resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def generate_comparative_feedback( #route 2 comparative feedback
    scene: str,
    intent: dict,
    composition_flags: Optional[list[str]] = None
) -> str:
    flags = composition_flags or []
    system_prompt = (
        "You are Throughline, a photography mentor who compares a user's stated intent "
        "with what the photo actually conveys, including composition notes."
    )
    user_prompt = (
        f"User Intent:\n{json.dumps(intent, indent=2)}\n\n"
        f"Image Description:\n{scene}\n\n"
    )
    if flags:
        user_prompt += "Composition Notes:\n- " + "\n- ".join(flags) + "\n\n"
    user_prompt += (
        "Please provide a single, concise paragraph that tells the user how well their intent "
        "was realized in the image, points out one or two areas to improve, and gives a concrete tip."
    )

    payload = {
        "model":"open-mistral-7b",
        "temperature":0.5,
        "messages":[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ]
    }

    resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

