"""Bridge between pywebview frontend and Jev Python client/models."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import webview

from jev import __version__
from jev.client import JevClient, JevClientError
from jev.config import (
    Credentials,
    clear_credentials,
    get_credentials_path,
    load_credentials,
    save_credentials,
)
from jev.models import ChoiceQuestion, Decision, NoulQuestion, Question, ScoreQuestion
from jev.presets import PRESETS


def mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "****"
    return f"{secret[:4]}...{secret[-4:]}"


class JevBridge:
    """JS API bridge exposed to the webview window."""

    def __init__(
        self,
        client: Optional[JevClient] = None,
        window: Any = None,
    ) -> None:
        self._client = client
        self._window = window

    def set_window(self, window: Any) -> None:
        """Associate the pywebview window instance with the bridge."""
        self._window = window

    def _get_window(self) -> Any:
        if self._window is not None:
            return self._window
        if getattr(webview, "windows", None):
            return webview.windows[0]
        return None

    def export_file(
        self,
        content: str,
        filename: str = "jev-suite.json",
    ) -> Dict[str, Any]:
        """Open native save dialog and write content to chosen file path."""
        window = self._get_window()
        if not window:
            return {
                "success": False,
                "error": "Desktop window not available",
            }

        try:
            result = window.create_file_dialog(
                dialog_type=webview.FileDialog.SAVE,
                save_filename=filename,
                file_types=("JSON files (*.json)", "All files (*.*)"),
            )
            if not result:
                return {"success": False, "cancelled": True}

            filepath = result[0] if isinstance(result, (list, tuple)) else str(result)
            target = Path(filepath)
            target.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(target)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_file(self) -> Dict[str, Any]:
        """Open native open dialog and read content from chosen file."""
        window = self._get_window()
        if not window:
            return {
                "success": False,
                "error": "Desktop window not available",
            }

        try:
            result = window.create_file_dialog(
                dialog_type=webview.FileDialog.OPEN,
                allow_multiple=False,
                file_types=("JSON files (*.json)", "All files (*.*)"),
            )
            if not result:
                return {"success": False, "cancelled": True}

            filepath = result[0] if isinstance(result, (list, tuple)) else str(result)
            target = Path(filepath)
            content = target.read_text(encoding="utf-8")
            return {"success": True, "content": content, "filename": target.name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Return credential and system status."""
        creds = load_credentials()
        cred_file = get_credentials_path()
        return {
            "version": __version__,
            "configured": creds is not None,
            "account_id": creds.account_id if creds else "",
            "api_token_masked": mask_secret(creds.api_token) if creds else "",
            "source": creds.source if creds else "none",
            "config_file": str(cred_file) if cred_file.exists() else None,
        }

    def test_credentials(self, account_id: str, api_token: str) -> Dict[str, Any]:
        """Test credentials against Cloudflare Workers AI without saving."""
        account_id = (account_id or "").strip()
        api_token = (api_token or "").strip()
        if not account_id or not api_token:
            return {"valid": False, "message": "Account ID and API Token cannot be empty"}

        client = JevClient(account_id=account_id, api_token=api_token)
        valid, msg = client.validate_credentials()
        return {"valid": valid, "message": msg}

    def save_credentials(self, account_id: str, api_token: str) -> Dict[str, Any]:
        """Validate and save credentials to config file."""
        account_id = (account_id or "").strip()
        api_token = (api_token or "").strip()
        if not account_id or not api_token:
            return {"success": False, "error": "Account ID and API Token cannot be empty"}

        client = JevClient(account_id=account_id, api_token=api_token)
        valid, msg = client.validate_credentials()
        if not valid:
            return {"success": False, "error": f"Cloudflare verification failed: {msg}"}

        path = save_credentials(account_id, api_token)
        self._client = client
        return {"success": True, "path": str(path)}

    def clear_credentials(self) -> Dict[str, Any]:
        """Clear saved config file credentials."""
        cleared = clear_credentials()
        self._client = None
        return {"success": cleared}

    def get_presets(self) -> List[Dict[str, Any]]:
        """Return pre-built demo scenarios with serializable questions."""
        presets_data = []
        for p in PRESETS:
            presets_data.append(
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "state": p.state,
                    "questions": {k: q.to_dict() for k, q in p.questions.items()},
                }
            )
        return presets_data

    def evaluate(self, state: Any, questions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate State against Question suite."""
        creds = load_credentials()
        if not creds:
            return {
                "success": False,
                "error": "No Cloudflare credentials found. Please configure credentials in Settings.",
            }

        client = self._client or JevClient(
            account_id=creds.account_id, api_token=creds.api_token
        )

        if not questions_data:
            return {
                "success": False,
                "error": "No Questions configured for evaluation.",
            }

        # Parse questions
        parsed_questions: Dict[str, Question] = {}
        for q_name, q_info in questions_data.items():
            q_type = q_info.get("type")
            instructions = q_info.get("instructions", "")
            if not instructions:
                return {
                    "success": False,
                    "error": f"Question '{q_name}' has empty instructions.",
                }

            if q_type == "noul":
                criteria = q_info.get("criteria")
                if criteria and (
                    not isinstance(criteria, dict)
                    or not criteria.get("true")
                    or not criteria.get("false")
                ):
                    criteria = None
                parsed_questions[q_name] = NoulQuestion(
                    instructions=instructions, criteria=criteria
                )

            elif q_type == "choice":
                criteria = q_info.get("criteria")
                if not isinstance(criteria, dict) or len(criteria) < 2:
                    return {
                        "success": False,
                        "error": f"Choice Question '{q_name}' must have at least 2 candidate options.",
                    }
                parsed_questions[q_name] = ChoiceQuestion(
                    instructions=instructions, criteria=criteria
                )

            elif q_type == "score":
                criteria = q_info.get("criteria")
                if not isinstance(criteria, list) or len(criteria) < 2:
                    return {
                        "success": False,
                        "error": f"Score Question '{q_name}' must have at least 2 ordered levels.",
                    }
                parsed_questions[q_name] = ScoreQuestion(
                    instructions=instructions, criteria=criteria
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown question primitive type '{q_type}' for '{q_name}'.",
                }

        try:
            decision = client.evaluate(state, parsed_questions)
            return {
                "success": True,
                "decision": decision.to_dict(),
            }
        except JevClientError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error during evaluation: {e}",
            }
