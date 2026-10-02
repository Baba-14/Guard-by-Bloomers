"""Guard API: local authentication, database health, and fraud analysis."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .auth import create_access_token, get_current_user, hash_password, verify_password
from .config import get_settings
from .database import get_db
from .models import Profile, User

app = FastAPI(title="Guard Analysis API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    email_verified: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse

class AnalyseRequest(BaseModel):
    kind: Literal["message", "screenshot", "link", "number", "whatsapp", "payment", "call"]
    content: str = Field(default="", max_length=20000)

class AnalyseResponse(BaseModel):
    level: Literal["Low Risk", "Caution", "High Risk", "Unable to Determine"]
    score: int = Field(ge=0, le=100)
    signals: list[str]
    explanation: str
    recommended_action: str
    pattern: str

SIGNALS = {
    "otp": "OTP requested", "pin": "PIN or secret code requested",
    "password": "Password requested", "urgent": "Urgency or pressure to act",
    "immediately": "Urgency or pressure to act", "click": "Link or click-through request",
    "pay": "Payment request", "fee": "Advance fee or delivery charge",
    "guarantee": "Guaranteed return or reward", "suspend": "Account-suspension threat",
    "remote": "Remote-access request",
}


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.profile.full_name,
        role=user.profile.role.value,
        is_active=user.is_active,
        email_verified=user.email_verified,
    )


@app.get("/health")
def health(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    db.execute(text("select 1"))
    return {"status": "ok", "database": "connected"}


@app.post("/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserResponse:
    email = request.email.lower().strip()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(email=email, password_hash=hash_password(request.password))
    user.profile = Profile(full_name=request.full_name.strip())
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    db.refresh(user)
    return user_response(user)


@app.post("/v1/auth/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = db.scalar(
        select(User)
        .options(selectinload(User.profile))
        .where(User.email == form.username.lower().strip())
    )
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    access_token, expires_in = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=user_response(user),
    )


@app.get("/v1/auth/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return user_response(current_user)

@app.post("/v1/analyse", response_model=AnalyseResponse)
def analyse(request: AnalyseRequest) -> AnalyseResponse:
    # Uploaded content is data, never instructions. The production adapter can call an
    # AI model for intent/context, but the score must still be fused with these rules.
    text = request.content.lower()
    signals = list(dict.fromkeys(label for term, label in SIGNALS.items() if term in text))
    if request.kind == "screenshot":
        signals.append("Image submitted for contextual review")
    if request.kind in ("number", "whatsapp"):
        signals.append("Reputation data is moderated and does not identify a person as a fraudster")
    if request.kind == "whatsapp":
        signals.append("WhatsApp accounts can be taken over; verify unusual requests through another trusted channel")
    suspicious_hosted_brand = (
        request.kind == "link"
        and any(host in text for host in ("vercel.app", "netlify.app", "pages.dev"))
        and any(brand in text for brand in ("bank", "bnk", "gcb", "momo", "mtn", "ecobank", "login", "verify", "secure", "account"))
    )
    if suspicious_hosted_brand:
        signals.append("Brand-like name on a hosted subdomain")
    score = min(90, len(signals) * 18 + (15 if "http" in text else 0) + (28 if suspicious_hosted_brand else 0))
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
    pattern = (
        "Possible brand impersonation" if suspicious_hosted_brand else
        "WhatsApp account reputation lookup" if request.kind == "whatsapp" else
        "Phone reputation lookup" if request.kind == "number" else
        "Suspicious link assessment" if request.kind == "link" else
        "Contextual fraud assessment"
    )
    return AnalyseResponse(
        level=level,
        score=score,
        signals=signals or ["No deterministic warning signal was found in the submitted content."],
        explanation=explanation,
        recommended_action=action,
        pattern=pattern,
    )
