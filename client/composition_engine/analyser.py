# client/composition_engine/analyzer.py

import cv2
import cv2.data
import numpy as np

# Load OpenCV's pretrained face cascade (make sure you have it in your environment)
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def analyze_composition(image_path: str) -> list[str]:
    """
    Returns a list of composition flags based on:
      - face/subject centering (rule of thirds)
      - cramping (subject too close to frame edges)
      - headroom (too much or too little above face)
    """
    flags = []
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    
    # Step 1: Face detection as proxy for subject
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) == 0:
        # no face detected → skip detailed checks
        return flags

    # For MVP, just take the largest face
    x, y, fw, fh = max(faces, key=lambda b: b[2]*b[3])
    cx, cy = x + fw/2, y + fh/2

    # Rule of thirds: does the face-center align with 1/3 or 2/3?
    thirds_x = [w/3, 2*w/3]
    thirds_y = [h/3, 2*h/3]
    if not any(abs(cx - tx) < w*0.05 for tx in thirds_x):
        flags.append("Subject not on vertical thirds")
    if not any(abs(cy - ty) < h*0.05 for ty in thirds_y):
        flags.append("Subject not on horizontal thirds")

    # Cramping: is the face too close (<5% of frame) to any edge?
    margin = 0.05
    if x / w < margin:
        flags.append("Subject cramped on left")
    if (x+fw) / w > 1 - margin:
        flags.append("Subject cramped on right")
    if y / h < margin:
        flags.append("Subject cramped at top")
    if (y+fh) / h > 1 - margin:
        flags.append("Subject cramped at bottom")

    # Headroom: too much space above the face?
    headroom_ratio = y / h
    if headroom_ratio > 0.3:
        flags.append("Too much headroom")
    elif headroom_ratio < 0.1:
        flags.append("Too little headroom")

    return flags
