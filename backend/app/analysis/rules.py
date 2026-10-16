"""Explainable, Ghana-aware message rules for the MVP risk engine."""

import re

from .schemas import EvidenceSignal


RULES: tuple[tuple[str, str, int, re.Pattern[str], str], ...] = (
    (
        "otp_request",
        "Requests a one-time password or verification code",
        55,
        re.compile(
            r"\b(?:send|share|provide|read|tell|forward|enter|confirm|give)\b.{0,45}"
            r"\b(?:otp|one[ -]?time (?:password|pin)|verification code|approval code)\b|"
            r"\b(?:otp|one[ -]?time (?:password|pin)|verification code|approval code)\b.{0,45}"
            r"\b(?:send|share|provide|read|tell|forward|enter|confirm|give)\b",
            re.I,
        ),
        "A legitimate support agent should not ask you to reveal an OTP.",
    ),
    (
        "pin_request",
        "Requests a PIN or secret code",
        55,
        re.compile(r"\b(?:send|share|provide|enter|tell|confirm)\b.{0,35}\b(?:pin|secret code)\b", re.I),
        "The message asks for a PIN or secret code.",
    ),
    (
        "password_request",
        "Requests a password",
        55,
        re.compile(r"\b(?:send|share|provide|enter|tell|confirm)\b.{0,35}\bpassword\b", re.I),
        "The message asks for a password.",
    ),
    (
        "card_security_code_request",
        "Requests a card CVV, CVC, or security code",
        55,
        re.compile(
            r"\b(?:send|share|provide|enter|tell|confirm|give)\b.{0,45}"
            r"\b(?:cvv|cvc|card security code|three[ -]?digit code)\b|"
            r"\b(?:cvv|cvc|card security code|three[ -]?digit code)\b.{0,45}"
            r"\b(?:send|share|provide|enter|tell|confirm|give)\b",
            re.I,
        ),
        "The CVV or CVC can authorize card-not-present payments and should not be disclosed.",
    ),
    (
        "card_details_request",
        "Requests sensitive payment-card details",
        40,
        re.compile(
            r"\b(?:send|share|provide|enter|tell|confirm|give)\b.{0,55}"
            r"\b(?:card number|card details|expiry date|expiration date|numbers? on (?:the )?(?:front|back) of (?:the )?card)\b",
            re.I,
        ),
        "Card numbers and expiry details should only be entered in a verified payment flow.",
    ),
    (
        "identity_details_request",
        "Requests identity details through an unverified message",
        22,
        re.compile(
            r"\b(?:send|share|provide|enter|reply with|confirm)\b.{0,55}"
            r"\b(?:ghana card (?:number|details)|national id|date of birth|bank account details)\b",
            re.I,
        ),
        "Sensitive identity information is being requested through the message.",
    ),
    (
        "urgency",
        "Uses urgency or pressure to act",
        10,
        re.compile(r"\b(?:urgent(?:ly)?|immediately|act now|within \d+ (?:minutes?|hours?)|last chance|today only)\b", re.I),
        "Pressure can be used to prevent independent verification.",
    ),
    (
        "fear_or_threat",
        "Threatens account suspension, arrest, or loss",
        18,
        re.compile(r"\b(?:account (?:will be )?(?:blocked|closed|suspended)|you will be arrested|legal action|lose access)\b", re.I),
        "The message uses a threat to force a quick decision.",
    ),
    (
        "advance_payment",
        "Requests an advance fee or Mobile Money payment",
        25,
        re.compile(r"\b(?:processing|release|clearance|delivery|registration) fee\b|\b(?:send|pay|transfer)\b.{0,45}\b(?:momo|mobile money|gh[₵c]|cedis?|fee)\b", re.I),
        "An upfront payment is requested before the promised benefit or service.",
    ),
    (
        "guaranteed_return",
        "Promises a guaranteed reward or return",
        30,
        re.compile(r"\b(?:guaranteed (?:\w+ ){0,2}(?:profit|returns?|reward)|double your money|you (?:have )?won|selected as (?:a )?winner)\b", re.I),
        "Unexpected winnings and guaranteed returns are common scam hooks.",
    ),
    (
        "investment_solicitation",
        "Solicits an investment using unusually strong profit claims",
        28,
        re.compile(
            r"\b(?:invest|investment|deposit|trading|forex|crypto)\b.{0,70}"
            r"\b(?:profit|returns?|earn|double|weekly|daily|no risk|risk[ -]?free)\b|"
            r"\b(?:profit|returns?|earn|double)\b.{0,70}\b(?:invest|investment|deposit|trading|forex|crypto)\b",
            re.I,
        ),
        "The message combines an investment request with unusually strong or rapid profit claims.",
    ),
    (
        "remote_access_request",
        "Requests remote access to a device",
        40,
        re.compile(r"\b(?:anydesk|teamviewer|remote access|screen share|install this app)\b", re.I),
        "Remote-access software can expose accounts, messages, and payment apps.",
    ),
    (
        "impersonation_claim",
        "Claims to represent a trusted institution or authority",
        16,
        re.compile(
            r"\b(?:calling|message|contact(?:ing)? you|writing) (?:from|on behalf of)\b.{0,45}"
            r"\b(?:bank|mtn|telecel|vodafone|government|police|court|ghana revenue|gra|ecg|school)\b|"
            r"\b(?:bank|mtn|telecel|vodafone|government|police|court|gra|ecg|mobile money|momo) (?:agent|official|support|team|desk|customer care)\b|"
            r"\bthis is (?:the )?.{0,30}(?:bank|mtn|telecel|vodafone|government|police|court|gra|ecg|mobile money|momo).{0,25}(?:support|customer care|fraud desk|security|office)\b",
            re.I,
        ),
        "The sender claims authority or a trusted identity that should be verified independently.",
    ),
    (
        "account_verification_link",
        "Directs account verification through a supplied link",
        28,
        re.compile(
            r"\b(?:click|open|visit|follow|sign in|log in)\b.{0,70}\b(?:link|url|https?://|www\.)|"
            r"\b(?:verify|update|unlock|restore|secure|link)\b.{0,45}\b(?:account|wallet|sim|ghana card|banking|profile)\b.{0,70}\b(?:link|url|https?://|www\.)",
            re.I,
        ),
        "The message directs a sensitive account action through a supplied link rather than a trusted app or saved address.",
    ),
    (
        "secrecy_request",
        "Asks you to keep the request secret",
        14,
        re.compile(r"\b(?:do not tell|don't tell|keep (?:this|it) secret|between (?:you and me|us)|tell nobody)\b", re.I),
        "Secrecy can isolate a target from people who could challenge the story.",
    ),
    (
        "momo_reversal",
        "Uses a Mobile Money reversal or mistaken-transfer story",
        32,
        re.compile(
            r"\b(?:wrong|mistaken|accidental) (?:momo|mobile money|transfer|number)\b|"
            r"\b(?:reverse|reversal|return|send back)\b.{0,45}\b(?:momo|mobile money|money|transfer|amount)\b",
            re.I,
        ),
        "Unexpected transfer and reversal stories should be verified with the provider before any money is returned.",
    ),
    (
        "fake_payment_claim",
        "Claims payment was made before independent confirmation",
        28,
        re.compile(
            r"\b(?:i have|we have|already) (?:paid|sent|transferred)\b.{0,65}\b(?:release|send|deliver|return|goods|item|money)\b|"
            r"\bpayment (?:alert|screenshot|proof|confirmation)\b.{0,45}\b(?:release|send|deliver)\b",
            re.I,
        ),
        "Payment screenshots and messages can be forged; confirm the balance in the official account or wallet.",
    ),
    (
        "account_takeover",
        "Shows a possible account-takeover request",
        24,
        re.compile(
            r"\b(?:new number|phone (?:is|was) lost|account (?:is|was) locked|help me receive|send (?:the )?code)\b",
            re.I,
        ),
        "A familiar account may have been taken over; verify with the person through another channel.",
    ),
    (
        "unusual_payment_destination",
        "Requests payment to a different or personal account",
        18,
        re.compile(
            r"\b(?:different|another|personal|my assistant'?s|my friend'?s)\b.{0,35}\b(?:number|account|wallet|momo)\b",
            re.I,
        ),
        "A changed payment destination can be a sign of impersonation or account compromise.",
    ),
)


def analyse_text(content: str) -> list[EvidenceSignal]:
    signals: list[EvidenceSignal] = []
    for key, label, weight, pattern, evidence in RULES:
        if pattern.search(content):
            signals.append(
                EvidenceSignal(
                    key=key,
                    label=label,
                    weight=weight,
                    confidence=1.0,
                    source="rule",
                    evidence=evidence,
                )
            )
    return signals
