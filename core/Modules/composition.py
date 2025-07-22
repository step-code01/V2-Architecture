import cv2
import numpy as np

class CompositionAnalyzer:
    def __init__(self, image, face_box):
        """
        image: loaded image (already resized)
        face_box: (x, y, w, h) from face detector
        """
        self.image = image.copy()
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        self.x, self.y, self.w, self.h = face_box
        self.face_box = face_box

        self.height, self.width = self.image.shape[:2]
        self.face_center = (self.x + self.w // 2, self.y + self.h // 2)

    def check_centering(self):
        """
        Checks if subject is horizontally centered.
        """
        subject_center_x = self.face_center[0]
        center_x = self.width // 2

        offset = subject_center_x - center_x
        offset_percent = (offset / (self.width / 2)) * 100

        if abs(offset_percent) < 20:
            return "✅ \t Subject is fairly centered horizontally."
        elif offset_percent < -20:
            return "❗\t Subject is too far left."
        else:
            return "❗\t Subject is too far right."

    def check_cramping(self, margin=30):
        """
        Checks if subject is too close to image borders.
        """
        if (
            self.x < margin or self.y < margin or
            (self.x + self.w) > (self.width - margin) or
            (self.y + self.h) > (self.height - margin)
        ):
            return "❗\t Subject is too close to the frame edge — might feel cramped."
        else:
            return "✅ \t Subject has enough breathing room."

    def check_rule_of_thirds(self, tolerance=40):
        """
        Checks if subject is aligned with rule-of-thirds grid.
        """
        thirds_x = [self.width // 3, 2 * self.width // 3]
        thirds_y = [self.height // 3, 2 * self.height // 3]
        face_x, face_y = self.face_center

        near_horizontal = any(abs(face_x - tx) < tolerance for tx in thirds_x)
        near_vertical = any(abs(face_y - ty) < tolerance for ty in thirds_y)

        if near_horizontal and near_vertical:
            return "✅ \t Subject is near rule-of-thirds intersection."
        elif near_horizontal or near_vertical:
            return "✅ \t Subject is roughly aligned to rule-of-thirds."
        else:
            return "❗\t Subject is not aligned to rule-of-thirds."

    def extract_edge_orientation_histogram(self, bins=18):
        """
        Returns histogram of edge orientations (structure)
        """
        sobel_x = cv2.Sobel(self.gray, cv2.CV_64F, 1, 0)
        sobel_y = cv2.Sobel(self.gray, cv2.CV_64F, 0, 1)

        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        angle = np.degrees(np.arctan2(sobel_y, sobel_x)) % 180

        angle_flat = angle.flatten()
        mag_flat = magnitude.flatten()

        hist, _ = np.histogram(angle_flat, bins=bins, range=(0, 180), weights=mag_flat)
        hist = hist / (np.sum(hist) + 1e-6)

        return hist

    def draw_rule_of_thirds_lines(self):
        """
        Draws the thirds grid on the image for visualization.
        """
        w, h = self.width, self.height
        image_copy = self.image.copy()

        # Vertical lines
        cv2.line(image_copy, (w//3, 0), (w//3, h), (0, 255, 0), 1)
        cv2.line(image_copy, (2*w//3, 0), (2*w//3, h), (0, 255, 0), 1)

        # Horizontal lines
        cv2.line(image_copy, (0, h//3), (w, h//3), (0, 255, 0), 1)
        cv2.line(image_copy, (0, 2*h//3), (w, 2*h//3), (0, 255, 0), 1)

        return image_copy

    def run_all(self):
        """
        Run all composition checks and return results as a dictionary.
        """
        return {
            "centering": self.check_centering(),
            "cramping": self.check_cramping(),
            "thirds": self.check_rule_of_thirds(),
            "edge_orientation_histogram": self.extract_edge_orientation_histogram()
        }
