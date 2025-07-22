import cv2
import numpy as np

def extract_color_temperature(image):
    # Step 1: Convert image to float for safe math
    image_float = image.astype(np.float32) / 255.0  # convert from 0–255 → 0.0–1.0 range

    # Step 2: Split into B, G, R channels (OpenCV uses BGR)
    B, G, R = cv2.split(image_float)

    # Step 3: Compute average intensity for R and B
    avg_r = np.mean(R)
    avg_b = np.mean(B)

    # Step 4: Compute warm-cool index: R minus B
    warm_cool_index = avg_r - avg_b  # positive = warm, negative = cool

    # Step 5: Interpret temperature
    if warm_cool_index > 0.05:
        temperature = "warm"
    elif warm_cool_index < -0.05:
        temperature = "cool"
    else:
        temperature = "neutral"

    # Step 6: Return both temperature and raw index
    return {
        "color_temperature": temperature, 
        "warm_cool_index": warm_cool_index
    }

'''
color temperature module
input - image -> output - temperature, warm_cool_index

'''


