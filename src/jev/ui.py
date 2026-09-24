"""Terminal UI rendering using Rich for Jev evaluation results."""

from __future__ import annotations

import json
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from jev.models import ChoiceAnswer, Decision, NoulAnswer, ScoreAnswer

console = Console()


def render_bar(probability: float, width: int = 24) -> str:
    """Render a text progress bar for a probability between 0.0 and 1.0."""
    clamped = max(0.0, min(1.0, probability))
    filled_len = int(round(clamped * width))
    empty_len = width - filled_len
    return f"[{'█' * filled_len}{'░' * empty_len}]"


def print_banner() -> None:
    banner_text = Text()
    banner_text.append("⚡ Jev Decision Model ", style="bold cyan")
    banner_text.append("· Cloudflare Workers AI\n", style="dim")
    banner_text.append(
        "Non-generative structured evaluation (Noul · Choice · Score)",
        style="italic dim white",
    )
    console.print(Panel(banner_text, border_style="cyan", padding=(1, 2)))


def print_state(state: Any) -> None:
    if isinstance(state, (dict, list)):
        formatted = json.dumps(state, indent=2, ensure_ascii=False)
        syntax = Syntax(formatted, "json", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="[bold]Evaluated State (Context)[/bold]", border_style="blue"))
    else:
        console.print(
            Panel(
                Text(str(state), style="white"),
                title="[bold]Evaluated State (Context)[/bold]",
                border_style="blue",
            )
        )


def print_decision(decision: Decision) -> None:
    console.print()
    header_table = Table.grid(expand=True)
    header_table.add_column(justify="left")
    header_table.add_column(justify="right")

    tokens_in = decision.usage.get("input_tokens", 0)
    tokens_out = decision.usage.get("output_tokens", 0)
    latency_str = f"{decision.latency_ms:.1f}ms" if decision.latency_ms > 0 else "N/A"

    header_table.add_row(
        Text.from_markup(f"[bold green]✔ Evaluation Completed[/bold green] · Model: [dim]{decision.model}[/dim]"),
        Text.from_markup(
            f"[dim]Latency:[/dim] [cyan]{latency_str}[/cyan] · "
            f"[dim]Tokens In/Out:[/dim] [cyan]{tokens_in}/{tokens_out}[/cyan]"
        ),
    )
    console.print(header_table)
    console.print()

    for name, answer in decision.answers.items():
        if isinstance(answer, NoulAnswer):
            _render_noul(name, answer)
        elif isinstance(answer, ChoiceAnswer):
            _render_choice(name, answer)
        elif isinstance(answer, ScoreAnswer):
            _render_score(name, answer)
        console.print()


def _render_noul(name: str, answer: NoulAnswer) -> None:
    prob = answer.probability
    pct = prob * 100.0
    bar = render_bar(prob, width=28)

    verdict_color = "green" if prob >= 0.5 else "red"
    verdict_label = "YES (True)" if prob >= 0.5 else "NO (False)"

    table = Table(title=f"Question: [bold cyan]{name}[/bold cyan] [dim](Noul / Binary)[/dim]", expand=True)
    table.add_column("Verdict", style="bold", width=14)
    table.add_column("Probability", width=32)
    table.add_column("Percentage", justify="right", width=12)

    table.add_row(
        Text(verdict_label, style=verdict_color),
        Text.from_markup(f"[{verdict_color}]{bar}[/{verdict_color}]"),
        f"{pct:.1f}%",
    )
    console.print(table)


def _render_choice(name: str, answer: ChoiceAnswer) -> None:
    table = Table(
        title=(
            f"Question: [bold cyan]{name}[/bold cyan] [dim](Choice / Classification)[/dim] "
            f"— Selected: [bold yellow]{answer.choice}[/bold yellow] "
            f"[dim](Confidence: {answer.confidence * 100:.1f}%)[/dim]"
        ),
        expand=True,
    )
    table.add_column("Candidate Option", style="bold", width=22)
    table.add_column("Probability Distribution", width=32)
    table.add_column("Probability", justify="right", width=12)

    # Sort descending by probability
    sorted_probs = sorted(
        answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    for option, prob in sorted_probs:
        pct = prob * 100.0
        bar = render_bar(prob, width=28)
        is_selected = option == answer.choice
        style_color = "green" if is_selected else "dim"

        table.add_row(
            Text(f"👉 {option}" if is_selected else f"   {option}", style=style_color),
            Text.from_markup(f"[{style_color}]{bar}[/{style_color}]"),
            Text(f"{pct:.1f}%", style=style_color),
        )
    console.print(table)


def _render_score(name: str, answer: ScoreAnswer) -> None:
    table = Table(
        title=(
            f"Question: [bold cyan]{name}[/bold cyan] [dim](Score / Ordinal Rating)[/dim] "
            f"— Calibrated Score: [bold magenta]{answer.score:.2f}[/bold magenta] "
            f"[dim](Confidence: {answer.confidence * 100:.1f}%)[/dim]"
        ),
        expand=True,
    )
    table.add_column("Ordinal Level", style="bold", width=30)
    table.add_column("Level Distribution", width=32)
    table.add_column("Probability", justify="right", width=12)

    # Map probability keys
    for key, prob in sorted(answer.probabilities.items(), key=lambda x: str(x[0])):
        label_text = answer.legend.get(str(key), f"Level {key}")
        display_label = f"[{key}] {label_text}"
        pct = prob * 100.0
        bar = render_bar(prob, width=28)

        # Highlight highest probability
        is_top = prob == max(answer.probabilities.values()) if answer.probabilities else False
        style_color = "magenta" if is_top else "dim"

        table.add_row(
            Text(display_label, style=style_color),
            Text.from_markup(f"[{style_color}]{bar}[/{style_color}]"),
            Text(f"{pct:.1f}%", style=style_color),
        )
    console.print(table)


def print_raw_json(raw: Dict[str, Any]) -> None:
    syntax = Syntax(
        json.dumps(raw, indent=2, ensure_ascii=False),
        "json",
        theme="monokai",
        line_numbers=True,
    )
    console.print(Panel(syntax, title="Raw Cloudflare API Response", border_style="dim"))
