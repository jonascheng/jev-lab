"""Main CLI entrypoint and interactive wizard for Jev."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import questionary
from rich.console import Console

from jev.client import JevAPIError, JevAuthenticationError, JevClient, JevClientError
from jev.config import (
    Credentials,
    clear_credentials,
    get_credentials_path,
    load_credentials,
    save_credentials,
)
from jev.models import ChoiceQuestion, NoulQuestion, Question, ScoreQuestion
from jev.presets import PRESETS
from jev.ui import (
    console,
    print_banner,
    print_decision,
    print_raw_json,
    print_state,
)


def mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "****"
    return f"{secret[:4]}...{secret[-4:]}"


def ensure_credentials() -> Optional[Credentials]:
    """Check credentials, prompt interactive setup if missing."""
    creds = load_credentials()
    if creds:
        return creds

    console.print(
        "\n[yellow]⚠️  No Cloudflare credentials found in environment or config file.[/yellow]"
    )
    console.print(
        "To evaluate the Jev model, please provide your Cloudflare Account ID and API Token."
    )
    console.print(
        "[dim]Note: Your API token requires Workers AI permissions. Token will be saved locally to ~/.config/jev/credentials.json (mode 0600).[/dim]\n"
    )

    return prompt_and_save_credentials()


def prompt_and_save_credentials() -> Optional[Credentials]:
    while True:
        account_id = questionary.text(
            "Enter your Cloudflare Account ID:",
            validate=lambda text: len(text.strip()) > 0 or "Account ID cannot be empty",
        ).ask()
        if account_id is None:
            return None

        api_token = questionary.password(
            "Enter your Cloudflare API Token:",
            validate=lambda text: len(text.strip()) > 0 or "API Token cannot be empty",
        ).ask()
        if api_token is None:
            return None

        console.print("[dim]Verifying credentials against Cloudflare Workers AI...[/dim]")
        client = JevClient(account_id=account_id, api_token=api_token)
        is_valid, msg = client.validate_credentials()

        if is_valid:
            path = save_credentials(account_id, api_token)
            console.print(f"[bold green]✔ Credentials verified and saved to {path} (0600)[/bold green]\n")
            return Credentials(account_id=account_id, api_token=api_token, source="config_file")
        else:
            console.print(f"[bold red]✖ Verification failed:[/bold red] {msg}\n")
            retry = questionary.confirm("Would you like to try entering credentials again?", default=True).ask()
            if not retry:
                return None


def run_preset_flow(client: JevClient) -> None:
    choices = [f"{p.id}: {p.title}" for p in PRESETS]
    choices.append("⬅️  Back to Main Menu")

    choice = questionary.select(
        "Select a pre-built demo scenario to run:",
        choices=choices,
    ).ask()

    if not choice or choice.startswith("⬅️"):
        return

    preset_id = choice.split(":")[0]
    preset = next(p for p in PRESETS if p.id == preset_id)

    console.print(f"\n[bold cyan]▶ Running Scenario:[/bold cyan] {preset.title}")
    console.print(f"[dim]{preset.description}[/dim]\n")
    print_state(preset.state)

    console.print("[dim]Evaluating state against Choice, Score, and Noul questions...[/dim]")
    try:
        decision = client.evaluate(preset.state, preset.questions)
        print_decision(decision)

        view_raw = questionary.confirm("View raw Cloudflare API JSON response?", default=False).ask()
        if view_raw:
            print_raw_json(decision.raw_response)
    except JevClientError as e:
        console.print(f"[bold red]Evaluation failed:[/bold red] {e}")

    questionary.press_any_key_to_continue("Press any key to return to menu...").ask()


def input_custom_state() -> Optional[Any]:
    method = questionary.select(
        "How would you like to provide the State to evaluate?",
        choices=[
            "1. Enter plain text / string inline",
            "2. Load JSON or text from local file path",
            "3. Compose in system $EDITOR (temporary JSON file)",
            "⬅️  Cancel",
        ],
    ).ask()

    if not method or method.startswith("⬅️"):
        return None

    if method.startswith("1."):
        text = questionary.text("Enter state text:").ask()
        return text.strip() if text else None

    if method.startswith("2."):
        file_path_str = questionary.path("Enter file path:").ask()
        if not file_path_str:
            return None
        path = Path(file_path_str).expanduser()
        if not path.is_file():
            console.print(f"[red]File not found: {path}[/red]")
            return None
        content = path.read_text(encoding="utf-8")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    if method.startswith("3."):
        editor = os.getenv("EDITOR", "nano" if sys.platform != "win32" else "notepad")
        sample_json = {
            "title": "Example Subject",
            "body": "User submitted content to analyze",
        }
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            tmp.write(json.dumps(sample_json, indent=2))
            tmp_path = tmp.name

        try:
            subprocess.call([editor, tmp_path])
            edited_content = Path(tmp_path).read_text(encoding="utf-8")
            try:
                return json.loads(edited_content)
            except json.JSONDecodeError:
                return edited_content
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return None


def run_custom_flow(client: JevClient) -> None:
    state = input_custom_state()
    if state is None:
        return

    console.print("\n[bold]Current State configured:[/bold]")
    print_state(state)

    questions: Dict[str, Question] = {}

    while True:
        console.print(f"\n[cyan]Configured Questions ({len(questions)}):[/cyan]")
        for q_name, q_val in questions.items():
            console.print(f"  • [bold]{q_name}[/bold] ({q_val.type}): {q_val.instructions}")

        action = questionary.select(
            "What would you like to do?",
            choices=[
                "➕ Add a Question (Noul / Choice / Score)",
                "🚀 Execute Evaluation with Current Questions" if questions else "🚀 (Add at least 1 question first)",
                "⬅️  Cancel",
            ],
        ).ask()

        if not action or action.startswith("⬅️"):
            return

        if action.startswith("➕"):
            q_name = questionary.text("Question identifier key (e.g. 'is_urgent', 'topic'):").ask()
            if not q_name:
                continue

            q_type = questionary.select(
                f"Select primitive type for '{q_name}':",
                choices=[
                    "noul  (Binary Yes/No hypothesis probability)",
                    "choice (Multi-candidate classification)",
                    "score  (Ordinal scale rating)",
                ],
            ).ask()
            if not q_type:
                continue

            instructions = questionary.text("Evaluation instructions / question text:").ask()
            if not instructions:
                continue

            if q_type.startswith("noul"):
                use_criteria = questionary.confirm("Specify custom true/false criteria?", default=False).ask()
                criteria = None
                if use_criteria:
                    true_crit = questionary.text("Criteria for TRUE:").ask()
                    false_crit = questionary.text("Criteria for FALSE:").ask()
                    criteria = {"true": true_crit or "True", "false": false_crit or "False"}
                questions[q_name] = NoulQuestion(instructions=instructions, criteria=criteria)

            elif q_type.startswith("choice"):
                options_str = questionary.text(
                    "Enter comma-separated candidate keys (e.g. 'billing, technical, sales'):"
                ).ask()
                if not options_str:
                    continue
                keys = [k.strip() for k in options_str.split(",") if k.strip()]
                crit_dict: Dict[str, str] = {}
                for k in keys:
                    desc = questionary.text(f"Description / criteria for '{k}':").ask()
                    crit_dict[k] = desc or k
                questions[q_name] = ChoiceQuestion(instructions=instructions, criteria=crit_dict)

            elif q_type.startswith("score"):
                levels_str = questionary.text(
                    "Enter comma-separated ordinal levels in order (e.g. 'Low, Medium, High'):"
                ).ask()
                if not levels_str:
                    continue
                levels = [l.strip() for l in levels_str.split(",") if l.strip()]
                questions[q_name] = ScoreQuestion(instructions=instructions, criteria=levels)

        elif action.startswith("🚀") and questions:
            console.print("\n[dim]Sending evaluation to Jev model...[/dim]")
            try:
                decision = client.evaluate(state, questions)
                print_decision(decision)

                view_raw = questionary.confirm("View raw Cloudflare API JSON response?", default=False).ask()
                if view_raw:
                    print_raw_json(decision.raw_response)
            except JevClientError as e:
                console.print(f"[bold red]Evaluation failed:[/bold red] {e}")

            questionary.press_any_key_to_continue("Press any key to return...").ask()
            break


def run_manage_credentials_flow() -> None:
    creds = load_credentials()
    cred_file = get_credentials_path()

    console.print("\n[bold]Credential Status:[/bold]")
    if creds:
        console.print(f"  • Source: [cyan]{creds.source}[/cyan]")
        console.print(f"  • Account ID: [green]{creds.account_id}[/green]")
        console.print(f"  • API Token: [green]{mask_secret(creds.api_token)}[/green]")
        if cred_file.exists():
            console.print(f"  • File: {cred_file}")
    else:
        console.print("  • No credentials configured.")
    console.print()

    action = questionary.select(
        "Manage credentials:",
        choices=[
            "1. Update credentials",
            "2. Clear saved credentials file",
            "⬅️  Back to Main Menu",
        ],
    ).ask()

    if not action or action.startswith("⬅️"):
        return

    if action.startswith("1."):
        prompt_and_save_credentials()
    elif action.startswith("2."):
        if clear_credentials():
            console.print("[green]✔ Credentials removed.[/green]")
        else:
            console.print("[yellow]No credentials file was found to remove.[/yellow]")
        questionary.press_any_key_to_continue().ask()


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print_banner()
        console.print(
            "\n[bold]Usage:[/bold] jev [options]\n\n"
            "Interactive wizard for testing TypeSafe's Jev decision model on Cloudflare Workers AI.\n\n"
            "[bold]Options:[/bold]\n"
            "  -h, --help      Show this help message and exit\n"
            "  -v, --version   Show version and exit\n\n"
            "[bold]Environment Variables:[/bold]\n"
            "  CLOUDFLARE_ACCOUNT_ID   Cloudflare Account ID\n"
            "  CLOUDFLARE_API_TOKEN    Cloudflare API Token\n\n"
            "[bold]Config File:[/bold]\n"
            "  ~/.config/jev/credentials.json (mode 0600)\n"
        )
        sys.exit(0)

    if "--version" in sys.argv or "-v" in sys.argv:
        from jev import __version__
        console.print(f"jev version {__version__}")
        sys.exit(0)

    print_banner()

    creds = ensure_credentials()
    if not creds:
        console.print("[red]Cannot proceed without credentials. Exiting.[/red]")
        sys.exit(1)

    client = JevClient(account_id=creds.account_id, api_token=creds.api_token)

    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "🎯 Run Pre-built Preset Demos (Support, Moderation, Fraud)",
                "🧪 Custom Evaluation Playground (Choice / Score / Noul)",
                "🔑 Manage Credentials",
                "❌ Exit",
            ],
        ).ask()

        if not choice or choice.startswith("❌"):
            console.print("[dim]Goodbye![/dim]")
            break

        if choice.startswith("🎯"):
            run_preset_flow(client)
        elif choice.startswith("🧪"):
            run_custom_flow(client)
        elif choice.startswith("🔑"):
            run_manage_credentials_flow()
            # Refresh client with potentially updated credentials
            updated_creds = load_credentials()
            if updated_creds:
                client = JevClient(
                    account_id=updated_creds.account_id,
                    api_token=updated_creds.api_token,
                )


if __name__ == "__main__":
    main()
