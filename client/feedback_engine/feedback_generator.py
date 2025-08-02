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
        "You are Throughline, a friendly photography mentor with 20+ years of experience. "
        "You help photographers bridge the gap between their creative vision and their final image. "
        "Given scene context, creative styles, and technical settings, provide a concise piece of advice "
        "that highlights one style and explains how to execute it well. Sound Natural and human like a teacher who is teaching the user"
        "who gives practical " \
        "actually useful tips that actually make a difference. Approach the problem step by step and achieve the" \
        "desired outcome.Don't be too poetic just be natural and human. You need to pose actually useful rather than a gimmick." \
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
    user_prompt += (
        "\nRespond with one encouraging paragraph that picks a style, mentions key settings, "
        "and includes a compositional tip."
    )

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
    intent: dict[str, str],
    composition_flags: Optional[list[str]] = None) -> str:
    flags = composition_flags or []

    # Fallback-safe defaults for missing fields
    intent = {
    "mood": intent.get("mood", "neutral"),
    "subject": intent.get("subject", "unspecified"),
    "tone": intent.get("tone", "balanced"),
    "focus": intent.get("focus", "center")
    }
    system_prompt = (
        "You are Throughline, a thoughtful photography mentor. "
        "Based on the photographer's stated intent and the image description, respond naturally & human-like answers short phrases: "
        "- If the photo aligns well with the intent, start by celebrating strengths and explaining why. "
        "- If the photo diverges, point out one area to improve and give a concrete tip." \
        "The most important thing is to sound natural and human, don't be over-poetic."
    )
    user_prompt = (
        f"User Intent:\n"
        f"- Mood: {intent['mood']}\n"
        f"- Subject: {intent['subject']}\n"
        f"- Tone: {intent['tone']}\n"
        f"- Focus: {intent['focus']}\n\n"
        f"Image Description:\n{scene}\n\n"
    )
    
    if flags:
        user_prompt += "Composition Notes:\n- " + "\n- ".join(flags) + "\n\n"
    user_prompt += (
        "Please respond with a single, natural paragraph that which appreciates when the photo is actually good (do not blindly give guidance always) and why that works; "
        "and gentle guidance otherwise."
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

