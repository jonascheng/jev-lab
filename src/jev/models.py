"""Domain data models and primitive definitions for Jev evaluations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class QuestionType(str, Enum):
    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


@dataclass
class NoulQuestion:
    instructions: str
    criteria: Optional[Dict[str, str]] = None
    type: str = "noul"

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "type": self.type,
            "instructions": self.instructions,
        }
        if self.criteria:
            data["criteria"] = self.criteria
        return data


@dataclass
class ChoiceQuestion:
    instructions: str
    criteria: Dict[str, str]
    type: str = "choice"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "instructions": self.instructions,
            "criteria": self.criteria,
        }


@dataclass
class ScoreQuestion:
    instructions: str
    criteria: List[str]
    type: str = "score"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "instructions": self.instructions,
            "criteria": self.criteria,
        }


Question = Union[NoulQuestion, ChoiceQuestion, ScoreQuestion]


@dataclass
class NoulAnswer:
    noul: float
    type: str = "noul"

    @property
    def probability(self) -> float:
        return self.noul


@dataclass
class ChoiceAnswer:
    choice: str
    confidence: float
    probabilities: Dict[str, float]
    type: str = "choice"


@dataclass
class ScoreAnswer:
    score: float
    confidence: float
    probabilities: Dict[str, float]
    legend: Dict[str, str] = field(default_factory=dict)
    type: str = "score"


Answer = Union[NoulAnswer, ChoiceAnswer, ScoreAnswer]


@dataclass
class Decision:
    model: str
    answers: Dict[str, Answer]
    usage: Dict[str, int]
    latency_ms: float = 0.0
    raw_response: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_response(
        cls, data: Dict[str, Any], latency_ms: float = 0.0
    ) -> Decision:
        model_name = data.get("model", "typesafe/jev")
        answers_dict: Dict[str, Answer] = {}

        raw_answers = data.get("answers", {})
        for name, ans_data in raw_answers.items():
            ans_type = ans_data.get("type")
            if ans_type == "noul":
                answers_dict[name] = NoulAnswer(
                    noul=float(ans_data.get("noul", 0.0))
                )
            elif ans_type == "choice":
                answers_dict[name] = ChoiceAnswer(
                    choice=str(ans_data.get("choice", "")),
                    confidence=float(ans_data.get("confidence", 0.0)),
                    probabilities={
                        k: float(v)
                        for k, v in ans_data.get("probabilities", {}).items()
                    },
                )
            elif ans_type == "score":
                answers_dict[name] = ScoreAnswer(
                    score=float(ans_data.get("score", 0.0)),
                    confidence=float(ans_data.get("confidence", 0.0)),
                    probabilities={
                        k: float(v)
                        for k, v in ans_data.get("probabilities", {}).items()
                    },
                    legend={
                        str(k): str(v)
                        for k, v in ans_data.get("legend", {}).items()
                    },
                )

        return cls(
            model=model_name,
            answers=answers_dict,
            usage=data.get("usage", {}),
            latency_ms=latency_ms,
            raw_response=data,
        )
