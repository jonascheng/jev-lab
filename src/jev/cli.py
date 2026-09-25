"""Main CLI entrypoint for Jev Desktop Studio."""

from __future__ import annotations

import importlib.resources
import sys
from pathlib import Path

import webview
from rich.console import Console

from jev import __version__
from jev.bridge import JevBridge
from jev.ui import print_banner

console = Console()


def get_html_content() -> str:
    """Load embedded single-file HTML for the webview UI."""
    try:
        return (
            importlib.resources.files("jev.web")
            .joinpath("index.html")
            .read_text(encoding="utf-8")
        )
    except Exception:
        fallback_path = Path(__file__).parent / "web" / "index.html"
        return fallback_path.read_text(encoding="utf-8")


def run_studio() -> None:
    """Launch the pywebview desktop window."""
    bridge = JevBridge()
    html = get_html_content()

    window = webview.create_window(
        title="Jev Studio — Decision Model Lab",
        html=html,
        js_api=bridge,
        width=1380,
        height=880,
        min_size=(1024, 680),
    )

    try:
        webview.start()
    except Exception as e:
        console.print(f"[bold red]Failed to start desktop webview:[/bold red] {e}")
        sys.exit(1)


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print_banner()
        console.print(
            "\n[bold]Usage:[/bold] jev [options]\n\n"
            "Desktop studio for TypeSafe Jev decision model on Cloudflare Workers AI.\n\n"
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
        console.print(f"jev version {__version__}")
        sys.exit(0)

    run_studio()


if __name__ == "__main__":
    main()
