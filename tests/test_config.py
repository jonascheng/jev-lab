"""Tests for credential loading, saving, and prioritization."""

import json
import os
import stat
from pathlib import Path

import pytest
from jev.config import (
    clear_credentials,
    get_credentials_path,
    load_credentials,
    save_credentials,
)


def test_env_var_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "env_acc_123")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "env_tok_abc")

    # Even if file exists, env vars should take precedence
    save_credentials("file_acc_456", "file_tok_def")

    creds = load_credentials()
    assert creds is not None
    assert creds.account_id == "env_acc_123"
    assert creds.api_token == "env_tok_abc"
    assert creds.source == "env"


def test_save_and_load_file_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)

    saved_path = save_credentials("acc_test_999", "tok_test_888")
    assert saved_path.is_file()

    # Check file permissions (0600)
    file_mode = stat.S_IMODE(saved_path.stat().st_mode)
    assert file_mode == (stat.S_IRUSR | stat.S_IWUSR)

    creds = load_credentials()
    assert creds is not None
    assert creds.account_id == "acc_test_999"
    assert creds.api_token == "tok_test_888"
    assert creds.source == "config_file"


def test_clear_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)

    save_credentials("acc_1", "tok_1")
    assert load_credentials() is not None

    deleted = clear_credentials()
    assert deleted is True
    assert load_credentials() is None
