# STEP 1: TEST FEEDBACK LOOP (Dummy logic for now)

# This is a dry-run simulation of the intent-feedback loop

def mock_extract_features(image_path):
    # Placeholder until we use real vision models
    return {
        "subject_centering": "off-center right",
        "edge_flow": "left-to-right diagonal",
        "light_balance": "strong backlight"
    }

def mock_parse_intent(user_input):
    # Dummy token parsing; replace with LLM later
    tokens = []
    if "drama" in user_input.lower():
        tokens.append("strong emotion")
    if "backlight" in user_input.lower():
        tokens.append("lighting priority")
    return tokens

def mock_feedback(intent_tokens, visual_features):
    # Dummy rule-based feedback (to be replaced by LLM)
    feedback = []
    if "lighting priority" in intent_tokens:
        if "strong backlight" in visual_features["light_balance"]:
            feedback.append("✅ Lighting supports your intent.")
        else:
            feedback.append("⚠️ Try enhancing backlight to match your intent.")
    if "strong emotion" in intent_tokens:
        if "left-to-right diagonal" in visual_features["edge_flow"]:
            feedback.append("✅ Dynamic edge flow adds drama.")
    return feedback

if __name__ == "__main__":
    user_intent = input("What's your intent for this photo? ")
    image_path = "assets/sample.jpg"  # Placeholder

    visual = mock_extract_features(image_path)
    parsed = mock_parse_intent(user_intent)
    response = mock_feedback(parsed, visual)

    print("\n--- Feedback ---")
    for line in response:
        print(line)



'''More specifically, the code does this:

User enters photographic intent (like: "I want drama and strong backlight").

It simulates visual signal extraction (e.g., “backlight” or “edge flow”) — via a placeholder.

It tokenizes the intent (e.g., “drama”, “lighting priority”) — via a placeholder.

It gives basic feedback based on matching intent to visual cues (like: “✅ lighting supports your intent” or “⚠️ not matching intent”) — via rule-based logic.''''''