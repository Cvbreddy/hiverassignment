from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Iterable


INTENTS = (
    "billing_refund",
    "delivery_tracking",
    "technical_problem",
    "account_access",
    "product_information",
    "cancellation",
    "complaint",
    "other",
)


@dataclass(frozen=True)
class Example:
    text: str
    intent: str
    resolution: str
    public_reply: str


@dataclass(frozen=True)
class Prediction:
    intent: str
    confidence: float
    action: str
    escalation_reason: str
    reply: str
    evidence: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


RULES = {
    "billing_refund": ["refund", "refunded", "charged", "charge", "billing", "payment", "money back", "invoice"],
    "delivery_tracking": ["where is", "tracking", "shipment", "delivery", "delivered", "package", "order"],
    "technical_problem": ["not working", "broken", "error", "bug", "crash", "cannot", "can't", "login", "app"],
    "account_access": ["password", "locked", "access", "sign in", "signin", "account", "verify"],
    "product_information": ["how much", "price", "feature", "available", "do you offer", "compatib", "hours"],
    "cancellation": ["cancel", "stop", "unsubscribe", "close my"],
    "complaint": ["angry", "awful", "terrible", "unacceptable", "disappointed", "complaint", "frustrated"],
}

SENSITIVE = ("password", "ssn", "social security", "card number", "cvv", "credit card", "personal information")
HIGH_RISK = ("fraud", "stolen", "hacked", "lawsuit", "lawyer", "threat", "injury", "medical", "legal")


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def classify(text: str) -> tuple[str, float]:
    normalized = text.lower().strip()
    tokens = _tokens(normalized)
    scores = {intent: 0.0 for intent in INTENTS}
    for intent, phrases in RULES.items():
        for phrase in phrases:
            if " " in phrase and phrase in normalized:
                scores[intent] += 2.0
            elif " " not in phrase and phrase in tokens:
                scores[intent] += 1.0
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    intent, score = ranked[0]
    second = ranked[1][1]
    if score == 0:
        return "other", 0.25
    confidence = min(0.98, 0.55 + 0.08 * score + 0.05 * max(0.0, score - second))
    return intent, round(confidence, 3)


def _similarity(query: str, candidate: str) -> float:
    query_tokens = _tokens(query)
    candidate_tokens = _tokens(candidate)
    overlap = len(query_tokens & candidate_tokens) / max(1, len(query_tokens | candidate_tokens))
    sequence = SequenceMatcher(None, query.lower(), candidate.lower()).ratio()
    return 0.65 * overlap + 0.35 * sequence


class SupportAgent:
    def __init__(self, examples: Iterable[Example], brand: str = "Acme"):
        self.brand = brand
        self.examples = list(examples)

    def _evidence(self, text: str, intent: str, limit: int = 3) -> list[Example]:
        candidates = [example for example in self.examples if example.intent == intent]
        return sorted(candidates, key=lambda item: _similarity(text, item.text), reverse=True)[:limit]

    def predict(self, text: str) -> Prediction:
        intent, confidence = classify(text)
        evidence = self._evidence(text, intent)
        lower = text.lower()
        reasons: list[str] = []
        if confidence < 0.66:
            reasons.append("low intent confidence")
        if any(term in lower for term in SENSITIVE):
            reasons.append("asks for sensitive information that must not be shared publicly")
        if any(term in lower for term in HIGH_RISK):
            reasons.append("contains a high-risk complaint requiring human review")
        if intent in {"complaint", "other"}:
            reasons.append("policy is conservative for ambiguous or negative cases")
        action = "escalate" if reasons else "auto-handle"
        if evidence:
            best = evidence[0]
            reply = best.public_reply
            if action == "escalate":
                reply = f"I’m sorry you’re dealing with this. I’m routing this to a specialist who can help securely."
        else:
            reply = "Thanks for reaching out. A specialist will review this and get back to you."
        return Prediction(
            intent=intent,
            confidence=confidence,
            action=action,
            escalation_reason="; ".join(reasons) if reasons else "routine request with a close historical resolution",
            reply=reply,
            evidence=[item.resolution for item in evidence],
        )

    def predict_many(self, texts: Iterable[str]) -> list[Prediction]:
        return [self.predict(text) for text in texts]
