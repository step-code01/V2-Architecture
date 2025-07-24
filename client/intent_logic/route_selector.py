# client/intent_logic/route_selector.py

from .intent_parser import parse_intent

THRESHOLD = 0.7

def should_suggest(free_text: str) -> bool:
    # If empty, definitely suggest
    if not free_text or free_text.strip() == "":
        return True
    # Else parse and check confidence
    _, conf = parse_intent(free_text)
    return conf < THRESHOLD
