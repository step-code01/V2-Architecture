# mock_llm_client.py

class MockLLMClient:
    def chat_completion(self, prompt: str) -> str:
        """
        Simulates the response of an LLM by returning hardcoded output.
        This mock assumes you are testing with vague user input about a tree.
        """
        if "tree" in prompt.lower():
            return '''
            {
              "mood": "melancholy",
              "subject": "tree",
              "composition_hint": "wide shot, faded tones"
            }
            '''
        elif "happy" in prompt.lower():
            return '''
            {
              "mood": "joyful",
              "subject": "friends laughing",
              "composition_hint": "centered frame, sunny lighting"
            }
            '''
        else:
            return '''
            {
              "mood": "neutral",
              "subject": "undefined",
              "composition_hint": "default"
            }
            '''
