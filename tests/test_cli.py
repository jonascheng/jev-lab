"""Tests for CLI flags."""

import sys
import pytest
from jev.cli import main


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
