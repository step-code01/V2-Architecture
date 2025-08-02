# client/intent_logic/intent_parser.py

import os, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY  = os.getenv("MISTRAL_API_KEY")
API_URL  = "https://api.mistral.ai/v1/chat/completions"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def parse_intent(free_text: str) -> tuple[dict, float]:
    system = "You are an expert with 20+ years of experience at parsing photographic intent into JSON keys mood, subject, tone, focus, and all 360 degree" \
    "aspects of photography. Analyse the users" \
    "prompt trying to understand what are they trying to achieve with the photo they want to click. " \
    "Examples:" \
    "If they are unsure about what they want by saying examples like - 'I don't know" \
    "what I want' etc any filler or complex prompts, analyse and react accordingly." \
    "If they ask questions with 'I don't know why this looks good, could you tell me why?'" \
    "analyse accordingly that user doesn't know but wants to know why it looks good." \
    "" \
    "Since you are an expert in photography intent parsing, Your ONLY response must be a single, valid JSON object with keys: "
    "mood, subject, tone, focus, and confidence (between 0 and 1). Do NOT add explanation or extra lines. Just output the JSON only."
    user   = f"Convert this into JSON with keys mood, subject, tone, focus, and include a confidence score between 0 and 1:\n\n\"{free_text}\""
    payload = {
      "model":"open-mistral-7b",
      "temperature":0.0,
      "messages":[
        {"role":"system","content":system},
        {"role":"user","content":user}
      ]
    }
    resp = requests.post(API_URL, json=payload, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()["choices"][0]["message"]["content"]
    # Expect something like: {"mood":"…","subject":"…","tone":"…","focus":"…","confidence":0.85}
    import json
    parsed = json.loads(data)
    confidence = parsed.pop("confidence", 0.0)
    return parsed, confidence
