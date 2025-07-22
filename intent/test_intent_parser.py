# test_intent_parser.py

from intent_parser import IntentParser
from mock_llm_client import MockLLMClient

def run_tests():
    llm = MockLLMClient()
    parser = IntentParser(llm)

    samples = [
        "Make it feel lonely and distant, like a memory. The subject is a tree.",
        "Something full of childlike joy, maybe balloons in the sky.",
        "Just a plain photo.",
    ]

    for i, prompt in enumerate(samples):
        result = parser.parse_intent(prompt)
        print(f"\n--- Test Case {i+1} ---")
        print("Input:", prompt)
        print("Output:", result)

if __name__ == "__main__":
    run_tests()
