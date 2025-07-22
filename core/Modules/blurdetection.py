import cv2 
import numpy

def blur_detection_focus(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    print(f"Sharpness (Laplace variance): {variance:.2f}")
    return variance  # This line was missing - numpy int32 leak reason
