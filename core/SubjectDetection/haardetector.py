import cv2

# SubjectDetection/haardetector.py
import cv2
from .subjectdetector import BaseDetector

class HaarDetector(BaseDetector):
    def __init__(self, cascade_path="haarcascade_frontalface_default.xml"):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + cascade_path)

    def detect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) == 0:
            return None

        # Take the largest detected face
        x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
        #return (x, y, w, h)
        return (int(x), int(y), int(w), int(h))
