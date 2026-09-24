"""Pre-built evaluation presets showcasing Choice, Score, and Noul primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from jev.models import ChoiceQuestion, NoulQuestion, Question, ScoreQuestion


@dataclass
class Preset:
    id: str
    title: str
    description: str
    state: Any
    questions: Dict[str, Question]


PRESETS: List[Preset] = [
    Preset(
        id="support_triage",
        title="Support Ticket Triage (Billing / Technical / Frustration)",
        description="Evaluates customer message urgency, department assignment, and emotional state.",
        state={
            "ticket": {
                "id": "TCK-8092",
                "subject": "Duplicate charge on annual invoice",
                "message": (
                    "I was charged twice on my card this morning for order #INV-8821. "
                    "I need an immediate refund for the duplicate transaction! "
                    "This is the second time your payment system glitched on my company."
                ),
                "customer_tier": "enterprise",
            }
        },
        questions={
            "refund_requested": NoulQuestion(
                instructions="Does `ticket.message` explicitly request a monetary refund?",
                criteria={
                    "true": "Customer explicitly asks for money back or refund",
                    "false": "No refund requested",
                },
            ),
            "department": ChoiceQuestion(
                instructions="Which team should handle this ticket?",
                criteria={
                    "billing": "Payments, invoices, duplicate charges, refunds, receipts",
                    "technical": "Software bugs, API outages, integrations, crashes",
                    "sales": "Plan upgrades, contract negotiations, new licenses",
                },
            ),
            "customer_frustration": ScoreQuestion(
                instructions="Rate the customer frustration level based on tone and phrasing.",
                criteria=[
                    "Calm and polite inquiry",
                    "Annoyed, urgent, or distressed",
                    "Extremely angry, aggressive, or threatening to leave",
                ],
            ),
        },
    ),
    Preset(
        id="content_moderation",
        title="Content Moderation (Harassment & Threat Detection)",
        description="Screens user posts for policy violations, category classification, and severity rating.",
        state={
            "post": {
                "author": "anon_914",
                "content": (
                    "You are completely useless and nobody here wants your pathetic contributions. "
                    "Get out of this forum before we track your address and dox your family."
                ),
                "channel": "public-forum",
                "reported_by_users": 4,
            }
        },
        questions={
            "policy_violation": NoulQuestion(
                instructions="Does `post.content` violate community safety guidelines against threats or harassment?",
                criteria={
                    "true": "Direct harassment, doxxing threat, or intimidation",
                    "false": "Acceptable constructive debate or critique",
                },
            ),
            "violation_category": ChoiceQuestion(
                instructions="Classify the primary policy violation category.",
                criteria={
                    "harassment_threats": "Direct personal insults, threats of violence, doxxing",
                    "hate_speech": "Attacks targeting protected identity attributes",
                    "spam": "Repetitive promotional advertising or phishing links",
                    "safe": "No violations detected",
                },
            ),
            "severity_level": ScoreQuestion(
                instructions="Rate the severity level to guide automated enforcement.",
                criteria=[
                    "Low: Mild incivility, soft warning suggested",
                    "Moderate: Clear violation, temporary post hide required",
                    "Critical: Credible threat or doxxing, immediate account suspension",
                ],
            ),
        },
    ),
    Preset(
        id="fraud_review",
        title="Financial Fraud & Transaction Review",
        description="Analyzes transaction metadata to determine fraud probability and mitigation action.",
        state={
            "transaction": {
                "id": "tx_77209",
                "amount_usd": 2850.0,
                "card_country": "US",
                "ip_country": "NG",
                "device_fingerprint_known": False,
                "failed_attempts_last_hour": 3,
                "merchant_category": "electronics",
            }
        },
        questions={
            "is_fraudulent": NoulQuestion(
                instructions="Does the transaction profile indicate high likelihood of unauthorized or fraudulent card usage?",
                criteria={
                    "true": "High risk indicators present (location mismatch, failed attempts)",
                    "false": "Consistent with legitimate cardholder activity",
                },
            ),
            "recommended_action": ChoiceQuestion(
                instructions="Determine the automated risk mitigation action.",
                criteria={
                    "approve": "Acceptable risk profile; process transaction",
                    "step_up_auth": "Moderate risk; require 3D Secure / biometric verification",
                    "decline_and_freeze": "Critical risk; decline transaction and freeze card",
                },
            ),
            "risk_score": ScoreQuestion(
                instructions="Rate the overall transaction fraud risk level.",
                criteria=[
                    "Low risk: Verified device and consistent geographical origin",
                    "Medium risk: Moderate anomalies requiring secondary confirmation",
                    "High risk: Multiple critical red flags indicating fraud",
                ],
            ),
        },
    ),
]


def get_preset_by_id(preset_id: str) -> Preset:
    for p in PRESETS:
        if p.id == preset_id:
            return p
    raise ValueError(f"Unknown preset id: {preset_id}")
