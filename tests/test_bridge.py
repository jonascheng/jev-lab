"""Tests for JevBridge JS API."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from jev.bridge import JevBridge, mask_secret
from jev.client import JevAPIError
from jev.config import Credentials
from jev.models import ChoiceAnswer, Decision, NoulAnswer, ScoreAnswer


def test_mask_secret():
    assert mask_secret("") == "****"
    assert mask_secret("short") == "****"
    assert mask_secret("12345678") == "****"
    assert mask_secret("123456789") == "1234...6789"


def test_get_status_unconfigured(monkeypatch):
    monkeypatch.setattr("jev.bridge.load_credentials", lambda: None)
    monkeypatch.setattr("jev.bridge.get_credentials_path", lambda: Path("/nonexistent/creds.json"))

    bridge = JevBridge()
    status = bridge.get_status()

    assert status["configured"] is False
    assert status["account_id"] == ""
    assert status["api_token_masked"] == ""
    assert status["source"] == "none"


def test_get_status_configured(monkeypatch):
    monkeypatch.setattr(
        "jev.bridge.load_credentials",
        lambda: Credentials(account_id="cf_acc_123", api_token="cf_tok_secret_value", source="env"),
    )
    monkeypatch.setattr("jev.bridge.get_credentials_path", lambda: Path("/tmp/creds.json"))

    bridge = JevBridge()
    status = bridge.get_status()

    assert status["configured"] is True
    assert status["account_id"] == "cf_acc_123"
    assert status["api_token_masked"] == "cf_t...alue"
    assert status["source"] == "env"


def test_test_credentials_empty():
    bridge = JevBridge()
    res = bridge.test_credentials("", "")
    assert res["valid"] is False


def test_test_credentials(monkeypatch):
    mock_client = MagicMock()
    mock_client.validate_credentials.return_value = (True, "OK")
    monkeypatch.setattr("jev.bridge.JevClient", lambda account_id, api_token: mock_client)

    bridge = JevBridge()
    res = bridge.test_credentials("acc123", "tok456")
    assert res["valid"] is True
    assert res["message"] == "OK"


def test_save_credentials_success(monkeypatch):
    mock_client = MagicMock()
    mock_client.validate_credentials.return_value = (True, "OK")
    monkeypatch.setattr("jev.bridge.JevClient", lambda account_id, api_token: mock_client)
    monkeypatch.setattr("jev.bridge.save_credentials", lambda acc, tok: Path("/saved/path.json"))

    bridge = JevBridge()
    res = bridge.save_credentials("acc123", "tok456")
    assert res["success"] is True
    assert res["path"] == "/saved/path.json"


def test_save_credentials_invalid(monkeypatch):
    mock_client = MagicMock()
    mock_client.validate_credentials.return_value = (False, "Invalid token")
    monkeypatch.setattr("jev.bridge.JevClient", lambda account_id, api_token: mock_client)

    bridge = JevBridge()
    res = bridge.save_credentials("acc123", "bad_token")
    assert res["success"] is False
    assert "Invalid token" in res["error"]


def test_clear_credentials(monkeypatch):
    monkeypatch.setattr("jev.bridge.clear_credentials", lambda: True)
    bridge = JevBridge()
    res = bridge.clear_credentials()
    assert res["success"] is True


def test_get_presets():
    bridge = JevBridge()
    presets = bridge.get_presets()
    assert len(presets) >= 3
    assert any(p["id"] == "ot_hmi_normal" for p in presets)
    hmi = next(p for p in presets if p["id"] == "ot_hmi_normal")
    assert "questions" in hmi
    assert "anomaly_detected" in hmi["questions"]
    assert hmi["questions"]["anomaly_detected"]["type"] == "noul"


def test_evaluate_no_credentials(monkeypatch):
    monkeypatch.setattr("jev.bridge.load_credentials", lambda: None)
    bridge = JevBridge()
    res = bridge.evaluate("state", {"q": {"type": "noul", "instructions": "test"}})
    assert res["success"] is False
    assert "No Cloudflare credentials found" in res["error"]


def test_evaluate_no_questions(monkeypatch):
    monkeypatch.setattr(
        "jev.bridge.load_credentials",
        lambda: Credentials(account_id="acc", api_token="tok", source="env"),
    )
    bridge = JevBridge()
    res = bridge.evaluate("state", {})
    assert res["success"] is False
    assert "No Questions configured" in res["error"]


def test_evaluate_validation_errors(monkeypatch):
    monkeypatch.setattr(
        "jev.bridge.load_credentials",
        lambda: Credentials(account_id="acc", api_token="tok", source="env"),
    )
    bridge = JevBridge()

    # Empty instructions
    res = bridge.evaluate("state", {"q": {"type": "noul", "instructions": ""}})
    assert res["success"] is False
    assert "empty instructions" in res["error"]

    # Choice < 2 options
    res = bridge.evaluate(
        "state",
        {"q": {"type": "choice", "instructions": "test", "criteria": {"only_one": "desc"}}},
    )
    assert res["success"] is False
    assert "at least 2 candidate options" in res["error"]

    # Score < 2 levels
    res = bridge.evaluate(
        "state",
        {"q": {"type": "score", "instructions": "test", "criteria": ["single"]}},
    )
    assert res["success"] is False
    assert "at least 2 ordered levels" in res["error"]

    # Unknown type
    res = bridge.evaluate(
        "state",
        {"q": {"type": "unknown", "instructions": "test"}},
    )
    assert res["success"] is False
    assert "Unknown question primitive" in res["error"]


def test_evaluate_success(monkeypatch):
    mock_client = MagicMock()
    decision = Decision(
        model="typesafe/jev",
        answers={
            "q1": NoulAnswer(noul=0.88),
            "q2": ChoiceAnswer(choice="a", confidence=0.9, probabilities={"a": 0.9, "b": 0.1}),
            "q3": ScoreAnswer(score=2.5, confidence=0.85, probabilities={"1": 0.1, "2": 0.8, "3": 0.1}),
        },
        usage={"input_tokens": 100, "output_tokens": 30},
        latency_ms=120.0,
        raw_response={"status": "ok"},
    )
    mock_client.evaluate.return_value = decision

    bridge = JevBridge(client=mock_client)
    res = bridge.evaluate(
        "Test State",
        {
            "q1": {"type": "noul", "instructions": "Is valid?", "criteria": {"true": "Yes", "false": "No"}},
            "q2": {"type": "choice", "instructions": "Pick one", "criteria": {"a": "Alpha", "b": "Beta"}},
            "q3": {"type": "score", "instructions": "Rate", "criteria": ["Low", "Mid", "High"]},
        },
    )

    assert res["success"] is True
    dec = res["decision"]
    assert dec["model"] == "typesafe/jev"
    assert dec["latency_ms"] == 120.0
    assert dec["answers"]["q1"]["type"] == "noul"
    assert dec["answers"]["q1"]["noul"] == 0.88
    assert dec["answers"]["q2"]["type"] == "choice"
    assert dec["answers"]["q2"]["choice"] == "a"
    assert dec["answers"]["q3"]["type"] == "score"
    assert dec["answers"]["q3"]["score"] == 2.5
    assert mock_client.evaluate.called


def test_evaluate_api_error(monkeypatch):
    mock_client = MagicMock()
    mock_client.evaluate.side_effect = JevAPIError("Bad Request from CF")
    bridge = JevBridge(client=mock_client)

    res = bridge.evaluate(
        "Test State",
        {
            "q1": {"type": "noul", "instructions": "Is valid?"},
        },
    )
    assert res["success"] is False
    assert "Bad Request from CF" in res["error"]


def test_export_file_no_window():
    bridge = JevBridge()
    res = bridge.export_file('{"test": true}', "test.json")
    assert res["success"] is False
    assert "Desktop window not available" in res["error"]


def test_export_file_cancelled():
    mock_window = MagicMock()
    mock_window.create_file_dialog.return_value = None

    bridge = JevBridge(window=mock_window)
    res = bridge.export_file('{"test": true}', "test.json")
    assert res["success"] is False
    assert res.get("cancelled") is True


def test_export_file_success(tmp_path):
    save_target = tmp_path / "exported.json"
    mock_window = MagicMock()
    mock_window.create_file_dialog.return_value = str(save_target)

    bridge = JevBridge(window=mock_window)
    res = bridge.export_file('{"saved": 123}', "exported.json")
    assert res["success"] is True
    assert res["path"] == str(save_target)
    assert save_target.read_text(encoding="utf-8") == '{"saved": 123}'


def test_export_file_tuple_result(tmp_path):
    save_target = tmp_path / "exported_tuple.json"
    mock_window = MagicMock()
    mock_window.create_file_dialog.return_value = (str(save_target),)

    bridge = JevBridge()
    bridge.set_window(mock_window)
    res = bridge.export_file('{"tuple": true}', "exported_tuple.json")
    assert res["success"] is True
    assert res["path"] == str(save_target)
    assert save_target.read_text(encoding="utf-8") == '{"tuple": true}'


def test_import_file_no_window():
    bridge = JevBridge()
    res = bridge.import_file()
    assert res["success"] is False
    assert "Desktop window not available" in res["error"]


def test_import_file_cancelled():
    mock_window = MagicMock()
    mock_window.create_file_dialog.return_value = None

    bridge = JevBridge(window=mock_window)
    res = bridge.import_file()
    assert res["success"] is False
    assert res.get("cancelled") is True


def test_import_file_success(tmp_path):
    source_file = tmp_path / "suite.json"
    source_file.write_text('{"imported": true}', encoding="utf-8")

    mock_window = MagicMock()
    mock_window.create_file_dialog.return_value = (str(source_file),)

    bridge = JevBridge(window=mock_window)
    res = bridge.import_file()
    assert res["success"] is True
    assert res["content"] == '{"imported": true}'
    assert res["filename"] == "suite.json"
