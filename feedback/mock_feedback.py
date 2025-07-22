# mock_feedback_module.py

class MockFeedbackModule:
    def generate_feedback(self, intent, signals=None):
        style = intent.get("style", "default")
        mood = intent.get("mood", "neutral")

        return (
            f"To enhance a {style} style with a {mood} mood, "
            f"consider adjusting contrast, color grading, and lighting accordingly."
        )
