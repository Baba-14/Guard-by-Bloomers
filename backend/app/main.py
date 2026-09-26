"""Guard analysis boundary. Deterministic signals remain authoritative; AI is contextual only."""
from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Guard Analysis API", version="0.1.0")

class AnalyseRequest(BaseModel):
    kind: Literal["message", "screenshot", "link", "number", "whatsapp", "payment", "call"]
    content: str = Field(default="", max_length=20000)

class AnalyseResponse(BaseModel):
    level: Literal["Low Risk", "Caution", "High Risk", "Unable to Determine"]
    score: int = Field(ge=0, le=100)
    signals: list[str]
    explanation: str
    recommended_action: str

SIGNALS = {
    "otp": "OTP requested", "pin": "PIN or secret code requested",
    "password": "Password requested", "urgent": "Urgency or pressure to act",
    "immediately": "Urgency or pressure to act", "click": "Link or click-through request",
    "pay": "Payment request", "fee": "Advance fee or delivery charge",
    "guarantee": "Guaranteed return or reward", "suspend": "Account-suspension threat",
    "remote": "Remote-access request",
}

@app.post("/v1/analyse", response_model=AnalyseResponse)
def analyse(request: AnalyseRequest) -> AnalyseResponse:
    # Uploaded content is data, never instructions. The production adapter can call an
    # AI model for intent/context, but the score must still be fused with these rules.
    text = request.content.lower()
    signals = list(dict.fromkeys(label for term, label in SIGNALS.items() if term in text))
    if request.kind == "screenshot":
        signals.append("Image submitted for contextual review")
    if request.kind == "whatsapp":
        signals.append("WhatsApp accounts can be taken over; verify unusual requests through another trusted channel")
    score = min(90, len(signals) * 18 + (15 if "http" in text else 0))
    level = "High Risk" if score >= 60 else "Caution" if score >= 30 else "Low Risk" if score == 0 else "Unable to Determine"
    explanation = {
        "High Risk": "Strong fraud indicators were detected in the submitted information.",
        "Caution": "Some suspicious or unverifiable signals were detected.",
        "Low Risk": "No strong deterministic fraud signal was detected in the information submitted.",
        "Unable to Determine": "Not enough information was available to make a confident assessment.",
    }[level]
    action = ("Do not share OTPs, PINs or more money. Pause contact and verify through an official channel."
              if level == "High Risk" else "No strong warning sign was found, but still verify unexpected requests before acting."
              if level == "Low Risk" else "Pause before responding. Verify independently before acting.")
    return AnalyseResponse(level=level, score=score, signals=signals or ["No deterministic warning signal found"], explanation=explanation, recommended_action=action)
