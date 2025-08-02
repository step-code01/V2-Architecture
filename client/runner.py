# client/runner.py

import os
import json
import requests
from dotenv import load_dotenv

from intent_logic.intent_parser     import parse_intent
from intent_logic.route_selector    import should_suggest
from style_engine.style_suggestor import suggest_styles
from style_engine.settings_mapper import map_settings
from feedback_engine.feedback_generator import generate_feedback
from composition_engine.analyser import analyze_composition

load_dotenv()

#resize image - server times out otherwise 
def prepare_image_for_upload(path, max_size=768):
    from PIL import Image
    import io

    img = Image.open(path)
    img.thumbnail((max_size, max_size))  # Maintain aspect ratio

    if img.mode != "RGB":
        img = img.convert("RGB")  # JPEG doesn't support alpha or palette modes

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)  # Compress
    buf.seek(0)
    return buf

# ——————————————————————————————————————————
# 1) Configuration
# ——————————————————————————————————————————

IMAGE_PATH = "Images/test2/20250802_134144.jpg"  # ← replace with your real local image path

# Read a free‑text intent from the user(harcoded right now, later from voice user)
FREE_TEXT_INTENT = "How can I improve the composition of this photo and feel better?"

#dynamic toggle switch now instead of manual button which was here

# Parse the raw free‑text into JSON + confidence
intent_data, confidence = parse_intent(FREE_TEXT_INTENT)
print(f" Parsed intent (conf={confidence:.2f}):", intent_data, "\n")

# New: log for debugging
print(f"[INFO] Parsed intent: {intent_data}, confidence: {confidence}")


# New: fallback routing
if not intent_data or confidence < 0.3:
    print("[WARN] Intent parsing failed or low confidence. Falling back to Route 1.")
    route = "suggestive"
else:
    print("[INFO] Valid intent parsed. Proceeding with Route 2.")
    route = "comparative"


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
    # Use resized image buffer in both routes
    img_buf = prepare_image_for_upload(IMAGE_PATH)
    files = {"image": img_buf}
    #files = {"image": ("image.jpg", img_buf, "image/jpeg")} image.jpg se kuch toh chudega idk

    #if not route1: #- check this or if-else?
    if route == "suggestive":
        # — Route 1: Suggestion Engine (Scene description only) —
        print(" Running Route 1 (no intent)…suggest styles\n")

        # 1) Natural Scene description
        #with open(IMAGE_PATH, "rb") as img_f: dangerous for big images full raw image bytes reading - not even req for LLM 
        data = {"prompt_text": FREE_TEXT_INTENT}
        resp = requests.post(DESCRIBE_URL, files=files, data=data, timeout=30) #10s timeout? 
        '''VERY IMPORTANTTT - verify=false abhi dev testing ke liye kiya DONT DEPLOY WITH THIS, NOT SAFE ONLY LOCAL TESTING'''
            #resp = requests.post(DESCRIBE_URL, files={"image": img_f}, timeout=30)
        resp.raise_for_status()

        scene_description = resp.json().get("image_description") #scene_description = resp.json()["image_description"]
        if not scene_description:
            raise RuntimeError("No scene description returned: " + resp.text)

        print(" Scene description (Route 1):\n")
        print(scene_description)

        # 2) Composition analysis
        composition_flags = analyze_composition(IMAGE_PATH)
        print("Composition flags:", composition_flags, "\n")

        # 3) Style suggestions
        styles = suggest_styles(scene_description, top_k=3) #style_suggestor plugged in
        print("Suggested styles:\n", styles, "\n")

        # 4) Settings mapping
        settings_per_style = map_settings(scene_description, styles) # Map each style to concrete camera settings
        print("Mapped settings per style:\n", json.dumps(settings_per_style, indent=2), "\n")

        final_advice = generate_feedback(
            scene=scene_description,
            styles=styles,
            settings=settings_per_style,
            composition_flags=composition_flags)
        
        print(" Final Advice:\n", final_advice)

    else:
        # — Route 2: Comparative Feedback (image + intent) —
        print(" Running Route 2 (confident with intent)… comparative feedback\n")

        # POST image + structured intent JSON to /parse
        #with open(IMAGE_PATH, "rb") as img_f:
        files = {"image": img_buf}
        data  = {"intent": json.dumps(intent_data)}
        resp = requests.post(PARSE_URL, files=files, data=data, timeout=30)
        '''VERY IMPORTANTTT - verify=false abhi dev testing ke liye kiya DONT DEPLOY WITH THIS, NOT SAFE ONLY LOCAL TESTING'''
        resp.raise_for_status()
        
        payload = resp.json()
        # server currently returns image_description + intent_text
        image_desc = payload.get("image_description", "—")
        intent_echo = payload.get("intent_text", "—")
        print(" LLaVA saw:\n", image_desc, "\n")
        print(" Intent was:\n", intent_echo, "\n")

        comp_flags = analyze_composition(IMAGE_PATH)
        print("Composition flags:", comp_flags, "\n")

        parsed_intent = {
        "mood": intent_data.get("mood", "neutral"),
        "subject": intent_data.get("subject", "unspecified"),
        "tone": intent_data.get("tone", "balanced"),
        "focus": intent_data.get("focus", "center")
        }

         # 3) Generate comparative feedback locally
        from feedback_engine.feedback_generator import generate_comparative_feedback
        comparative = generate_comparative_feedback(
        scene=image_desc,
        intent=parsed_intent,
        composition_flags=comp_flags
        )

        print(" Comparative Feedback:\n", comparative)

        # If you extend /parse to also return a "feedback" field, you could:
        #if "feedback" in payload:
           # print(" Feedback:\n", payload["feedback"])
        
        # ← And here you can later wrap in additional comparison or humanization:
        #    feedback = generate_comparative_feedback(payload)
        #    print("Feedback:\n", feedback)

except Exception as e:
    print(" Runner error:", repr(e))
