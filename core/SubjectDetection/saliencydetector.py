import cv2
import numpy as np
from .subjectdetector import BaseDetector

class SaliencyDetector(BaseDetector):
    def __init__(self):
        self.detector = cv2.saliency.StaticSaliencyFineGrained_create()

    def detect(self, image):
        success, saliency_map = self.detector.computeSaliency(image)
        if not success:
            return None

        saliency_map = (saliency_map * 255).astype("uint8")
        _, mask = cv2.threshold(saliency_map, 180, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        #return (x, y, w, h)
        return (int(x), int(y), int(w), int(h)) #to fix not showing output vector
