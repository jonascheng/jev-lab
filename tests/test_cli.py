"""Tests for CLI flags and studio launch."""

import sys
from unittest.mock import MagicMock
import pytest
from jev.cli import main, get_html_content


def test_cli_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["jev", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_cli_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["jev", "--version"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_get_html_content():
    content = get_html_content()
    assert "<!DOCTYPE html>" in content
    assert "JEV STUDIO" in content


def test_cli_launches_studio(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jev"])
    called = {}

    def mock_create_window(title, html, js_api, width, height, min_size):
        called["window"] = True
        called["js_api"] = js_api
        assert "Jev Studio" in title
        assert len(html) > 0
        assert js_api is not None
        mock_win = MagicMock()
        return mock_win

    def mock_start():
        called["start"] = True

    monkeypatch.setattr("webview.create_window", mock_create_window)
    monkeypatch.setattr("webview.start", mock_start)

    main()
    assert called.get("window") is True
    assert called.get("start") is True
    assert called["js_api"]._window is not None
