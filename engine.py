# throughline_engine.py

from intent.intent_parser import IntentParser
from intent.mock_llm_client import MockLLMClient
from feedback.mock_feedback import MockFeedbackModule

def main():
    # Set up the mock LLM client and parser
    llm_client = MockLLMClient()
    parser = IntentParser(llm_client)

    # Set up mock feedback module
    feedback_module = MockFeedbackModule() 

    print("Throughline Engine: MVP V2")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("User Intent: ")
        if user_input.strip().lower() == "exit":
            break

        # Step 1: Parse user intent using LLM
        intent = parser.parse_intent(user_input)
        print("\n🔍 Parsed Intent:")
        print(intent)

        # Step 2: Generate mock feedback
        feedback = feedback_module.generate_feedback(intent)
        print("\n📝 Feedback:")
        print(feedback)
        print()

if __name__ == "__main__":
    main()
