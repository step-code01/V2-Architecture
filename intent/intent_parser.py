# intent_parser.py

from typing import Dict

class IntentParser:
    def __init__(self, llm_client):
        """
        LLM-centric intent parser that relies entirely on a lightweight LLM (e.g., Mistral)
        to parse free-form user input into structured intent.
        """
        self.llm_client = llm_client

    def parse_intent(self, raw_text: str) -> Dict:
        """
        Sends raw user input to the LLM to extract structured intent.

        Args:
            raw_text (str): The raw text entered by the user.

        Returns:
            Dict: Parsed intent object like {
                "mood": "melancholy",
                "subject": "solitary tree",
                "composition_hint": "rule of thirds"
            }
        """
        prompt = self._build_prompt(raw_text)
        response = self.llm_client.chat_completion(prompt)
        return self._extract_json(response)

    def _build_prompt(self, user_input: str) -> str:
        return f"""
You are an assistant helping a photography agent understand creative intent.

The user will provide a vague or creative prompt. Your job is to extract structured fields from it.

Respond ONLY in JSON format with keys like:
- mood (string)
- subject (string)
- composition_hint (string)

Example Input: "Make it feel lonely and distant, like a memory. The subject is a tree."
Output:
{{
  "mood": "melancholy",
  "subject": "tree",
  "composition_hint": "wide shot, faded tones"
}}

Now parse this:
"{user_input}"
"""

    def _extract_json(self, llm_response: str) -> Dict:
        try:
            import json
            start = llm_response.find('{')
            end = llm_response.rfind('}') + 1
            return json.loads(llm_response[start:end])
        except:
            return {"type": "error", "value": llm_response}


#helping bridging the gap between intent and outcome