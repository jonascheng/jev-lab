"""Client for interacting with Cloudflare Workers AI typesafe/jev model."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple, Union

import httpx

from jev.models import Decision, Question


class JevClientError(Exception):
    """Base exception for Jev client errors."""


class JevAuthenticationError(JevClientError):
    """Raised when authentication with Cloudflare fails."""


class JevAPIError(JevClientError):
    """Raised when Cloudflare returns an API error."""


class JevClient:
    def __init__(
        self,
        account_id: str,
        api_token: str,
        model: str = "typesafe/jev",
        timeout: float = 30.0,
    ):
        self.account_id = account_id.strip()
        self.api_token = api_token.strip()
        self.model = model.strip()
        self.timeout = timeout
        self.base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run"
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "jev-cli/0.1.0",
        }

    def validate_credentials(self) -> Tuple[bool, str]:
        """
        Send a lightweight evaluation request to verify Account ID and API Token.
        Returns (is_valid, message).
        """
        payload = {
            "model": self.model,
            "input": {
                "state": "ping",
                "questions": {
                    "is_active": {
                        "type": "noul",
                        "instructions": "Is this an active system?",
                    }
                },
            },
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.base_url,
                    headers=self._headers(),
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", True):
                        return True, "Credentials verified successfully."
                    errors = data.get("errors", [])
                    msg = errors[0].get("message") if errors else "API error"
                    return False, f"Cloudflare API error: {msg}"
                elif response.status_code in (401, 403):
                    return (
                        False,
                        f"Authentication failed (HTTP {response.status_code}). Please verify your API token and Account ID.",
                    )
                else:
                    return (
                        False,
                        f"Validation failed (HTTP {response.status_code}): {response.text}",
                    )
        except httpx.RequestError as e:
            return False, f"Network connection error: {e}"

    def evaluate(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Dict[str, Union[Question, Dict[str, Any]]],
    ) -> Decision:
        """
        Evaluate state against a dict of questions.
        """
        formatted_questions: Dict[str, Any] = {}
        for name, q in questions.items():
            if isinstance(q, Question):
                formatted_questions[name] = q.to_dict()
            elif isinstance(q, dict):
                formatted_questions[name] = q
            else:
                raise ValueError(f"Invalid question type for '{name}': {type(q)}")

        payload = {
            "model": self.model,
            "input": {
                "state": state,
                "questions": formatted_questions,
            },
        }

        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.base_url,
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.RequestError as e:
            raise JevClientError(f"HTTP request failed: {e}") from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        if response.status_code in (401, 403):
            raise JevAuthenticationError(
                f"Cloudflare authentication failed (HTTP {response.status_code}). Check your API token."
            )
        elif response.status_code != 200:
            raise JevAPIError(
                f"Cloudflare Workers AI error (HTTP {response.status_code}): {response.text}"
            )

        resp_json = response.json()
        # Cloudflare wraps result in `result` field
        result_data = resp_json.get("result", resp_json)

        return Decision.from_api_response(result_data, latency_ms=latency_ms)
