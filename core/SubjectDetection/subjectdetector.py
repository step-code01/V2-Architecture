class BaseDetector:
    def detect(self, image):
        """
        Returns:
            - (x, y, w, h): bounding box of subject if detected
            - None if detection failed
        """
        raise NotImplementedError

class SubjectDetectorPipeline:
    def __init__(self, detectors):
        self.detectors = detectors  # list of detector instances

    def detect_subject(self, image):
        for detector in self.detectors:
            result = detector.detect(image)
            if result is not None:
                return result, detector.__class__.__name__
        return None, None
