"""Tests for JevClient HTTP interactions."""

import httpx
import pytest
from jev.client import (
    JevAPIError,
    JevAuthenticationError,
    JevClient,
    JevClientError,
)
from jev.models import NoulQuestion


def test_client_headers_and_url():
    client = JevClient(account_id="test_acc", api_token="test_tok")
    assert client.base_url == "https://api.cloudflare.com/client/v4/accounts/test_acc/ai/run"
    headers = client._headers()
    assert headers["Authorization"] == "Bearer test_tok"
    assert headers["Content-Type"] == "application/json"


def test_client_validation_success(monkeypatch):
    client = JevClient(account_id="acc_valid", api_token="tok_valid")

    def mock_post(url, headers, json):
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"success": True, "result": {"model": "typesafe/jev", "answers": {}}},
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "post", lambda self, *args, **kwargs: mock_post(*args, **kwargs))

    is_valid, msg = client.validate_credentials()
    assert is_valid is True
    assert "successfully" in msg


def test_client_validation_auth_failure(monkeypatch):
    client = JevClient(account_id="acc_bad", api_token="tok_bad")

    def mock_post(url, headers, json):
        request = httpx.Request("POST", url)
        return httpx.Response(
            401,
            json={"success": False, "errors": [{"message": "Invalid token"}]},
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "post", lambda self, *args, **kwargs: mock_post(*args, **kwargs))

    is_valid, msg = client.validate_credentials()
    assert is_valid is False
    assert "Authentication failed" in msg


def test_client_evaluate_success(monkeypatch):
    client = JevClient(account_id="acc_test", api_token="tok_test")

    mock_result = {
        "model": "typesafe/jev",
        "answers": {
            "is_test": {
                "type": "noul",
                "noul": 0.99,
            }
        },
        "usage": {"input_tokens": 10, "output_tokens": 2},
    }

    def mock_post(url, headers, json):
        assert json["model"] == "typesafe/jev"
        assert json["input"]["state"] == "hello"
        assert "is_test" in json["input"]["questions"]
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"result": mock_result, "success": True},
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "post", lambda self, *args, **kwargs: mock_post(*args, **kwargs))

    decision = client.evaluate(
        state="hello",
        questions={"is_test": NoulQuestion(instructions="Is hello?")},
    )

    assert decision.model == "typesafe/jev"
    assert "is_test" in decision.answers
    assert decision.answers["is_test"].noul == 0.99
    assert decision.latency_ms > 0
