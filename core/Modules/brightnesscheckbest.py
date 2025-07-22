import cv2
import numpy as np

'''best way to achieve what im doing with method overriding like java'''

class BrightnessChecker:
    def __init__(self, image):
        self.image = image
        self.gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def run(self):
        overall = np.mean(self.gray)
        print(f"Brightness (entire image): {overall:.2f}")
        return overall

class SubjectBrightnessChecker(BrightnessChecker):
    def __init__(self, image, face_box):
        super().__init__(image)
        self.face_box = face_box

    def run(self):  # ← This overrides the base method
        x, y, w, h = self.face_box
        face_roi = self.gray[y:y+h, x:x+w]
        face_brightness = np.mean(face_roi)
        overall = super().run()  # Optionally call base method too
        print(f"Brightness (face only): {face_brightness:.2f}")
        return {
            "overall_brightness": overall,
            "face_brightness": face_brightness
        }

'''method overriding se karring subject brightness'''