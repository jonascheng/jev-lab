"""Configuration and persistent credential management for Jev."""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Credentials:
    account_id: str
    api_token: str
    source: str = "config_file"  # "env" or "config_file"


def get_config_dir() -> Path:
    """Return path to config directory (~/.config/jev or $XDG_CONFIG_HOME/jev)."""
    xdg_config = os.getenv("XDG_CONFIG_HOME")
    if xdg_config:
        base_dir = Path(xdg_config)
    else:
        base_dir = Path.home() / ".config"
    return base_dir / "jev"


def get_credentials_path() -> Path:
    """Return path to credentials JSON file."""
    return get_config_dir() / "credentials.json"


def load_credentials() -> Optional[Credentials]:
    """
    Resolve credentials in priority order:
    1. Environment variables: CLOUDFLARE_ACCOUNT_ID & CLOUDFLARE_API_TOKEN
    2. Stored config file: ~/.config/jev/credentials.json
    """
    env_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    env_api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    if env_account_id and env_api_token:
        return Credentials(
            account_id=env_account_id.strip(),
            api_token=env_api_token.strip(),
            source="env",
        )

    cred_path = get_credentials_path()
    if cred_path.is_file():
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_account_id = data.get("account_id") or env_account_id
            file_api_token = data.get("api_token") or env_api_token
            if file_account_id and file_api_token:
                return Credentials(
                    account_id=str(file_account_id).strip(),
                    api_token=str(file_api_token).strip(),
                    source="config_file",
                )
        except Exception:
            pass

    return None


def save_credentials(account_id: str, api_token: str) -> Path:
    """
    Save credentials to ~/.config/jev/credentials.json with 0600 file permissions.
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    cred_path = get_credentials_path()

    payload = {
        "account_id": account_id.strip(),
        "api_token": api_token.strip(),
    }

    # Write file
    temp_path = cred_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Secure permissions (0600: read/write owner only)
    temp_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    temp_path.replace(cred_path)

    return cred_path


def clear_credentials() -> bool:
    """Delete credentials file if it exists."""
    cred_path = get_credentials_path()
    if cred_path.exists():
        cred_path.unlink()
        return True
    return False
