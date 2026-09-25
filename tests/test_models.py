"""Tests for Jev models and primitives."""

import pytest
from jev.models import (
    ChoiceAnswer,
    ChoiceQuestion,
    Decision,
    NoulAnswer,
    NoulQuestion,
    ScoreAnswer,
    ScoreQuestion,
)


def test_noul_question_serialization():
    q = NoulQuestion(instructions="Is this urgent?", criteria={"true": "Urgent", "false": "Calm"})
    d = q.to_dict()
    assert d["type"] == "noul"
    assert d["instructions"] == "Is this urgent?"
    assert d["criteria"] == {"true": "Urgent", "false": "Calm"}


def test_choice_question_serialization():
    q = ChoiceQuestion(
        instructions="Pick department",
        criteria={"billing": "Money matters", "tech": "Bugs"},
    )
    d = q.to_dict()
    assert d["type"] == "choice"
    assert d["instructions"] == "Pick department"
    assert d["criteria"] == {"billing": "Money matters", "tech": "Bugs"}


def test_score_question_serialization():
    q = ScoreQuestion(
        instructions="Rate frustration",
        criteria=["Calm", "Annoyed", "Furious"],
    )
    d = q.to_dict()
    assert d["type"] == "score"
    assert d["instructions"] == "Rate frustration"
    assert d["criteria"] == ["Calm", "Annoyed", "Furious"]


def test_decision_from_api_response():
    sample_response = {
        "model": "jev-1.13.0",
        "answers": {
            "is_urgent": {
                "type": "noul",
                "noul": 0.95,
            },
            "department": {
                "type": "choice",
                "choice": "billing",
                "confidence": 0.88,
                "probabilities": {
                    "billing": 0.88,
                    "technical": 0.12,
                },
            },
            "frustration": {
                "type": "score",
                "score": 1.45,
                "confidence": 0.92,
                "legend": {
                    "0": "Calm",
                    "1": "Annoyed",
                    "2": "Furious",
                },
                "probabilities": {
                    "0": 0.05,
                    "1": 0.90,
                    "2": 0.05,
                },
            },
        },
        "usage": {
            "input_tokens": 150,
            "output_tokens": 40,
        },
    }

    decision = Decision.from_api_response(sample_response, latency_ms=125.4)

    assert decision.model == "jev-1.13.0"
    assert decision.latency_ms == 125.4
    assert decision.usage["input_tokens"] == 150

    # Noul answer
    noul_ans = decision.answers["is_urgent"]
    assert isinstance(noul_ans, NoulAnswer)
    assert noul_ans.noul == 0.95
    assert noul_ans.probability == 0.95

    # Choice answer
    choice_ans = decision.answers["department"]
    assert isinstance(choice_ans, ChoiceAnswer)
    assert choice_ans.choice == "billing"
    assert choice_ans.confidence == 0.88
    assert choice_ans.probabilities["billing"] == 0.88

    # Score answer
    score_ans = decision.answers["frustration"]
    assert isinstance(score_ans, ScoreAnswer)
    assert score_ans.score == 1.45
    assert score_ans.legend["1"] == "Annoyed"
    assert score_ans.probabilities["1"] == 0.90

    # Decision serialization
    serialized = decision.to_dict()
    assert serialized["model"] == "jev-1.13.0"
    assert serialized["latency_ms"] == 125.4
    assert serialized["answers"]["is_urgent"]["type"] == "noul"
    assert serialized["answers"]["is_urgent"]["probability"] == 0.95
    assert serialized["answers"]["department"]["type"] == "choice"
    assert serialized["answers"]["department"]["choice"] == "billing"
    assert serialized["answers"]["frustration"]["type"] == "score"
    assert serialized["answers"]["frustration"]["score"] == 1.45
