from pydantic import BaseModel
from typing import List

class ImageParseRequest(BaseModel):
    image_base64: str  # We'll send the image encoded as base64

class ImageParseResponse(BaseModel):
    parsed_description: str  # e.g. "A foggy bridge scene with a man walking"

class MistralIntentRequest(BaseModel):
    prompt: str

class MistralIntentResponse(BaseModel):
    structured_intent: str

class FeedbackRequest(BaseModel):
    image_description: str
    user_intent: str

class FeedbackResponse(BaseModel):
    feedback: str
