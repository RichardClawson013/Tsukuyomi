"""
examples/demo_run.py — Scripted demo for Tsukuyomi.

Run it:
    pip install -e .
    python examples/demo_run.py
"""

import time
import tempfile
import pathlib

from tsukuyomi import ActionProposal, FakeEmailAdapter, FakeFileAdapter, FakeCalendarAdapter, EmailDraftAdapter

CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

SEP = BOLD + "─" * 60 + RESET


def line(text: str, color: str = "", indent: int = 0) -> None:
    prefix = "  " * indent
    print(color + prefix + text + RESET, flush=True)
    time.sleep(0.6)


def gap(n: float = 1.5) -> None:
    time.sleep(n)


def section(title: str) -> None:
    gap(2.0)
    print()
    print(SEP)
    line(title, BOLD)
    print(SEP)
    gap(1.0)


def show_dict(data: dict, color: str = DIM, indent: int = 1) -> None:
    import json
    for ln in json.dumps(data, indent=2).splitlines():
        line(ln, color, indent)


def main() -> None:
    gap(0.5)
    print()
    print(BOLD + "=" * 60 + RESET)
    print(BOLD + "Tsukuyomi — Illusion Layer Demo" + RESET)
    print(BOLD + "=" * 60 + RESET)
    line("The agent acts. You decide when it's real.", DIM)
    gap(2.0)

    # ── Scenario 1: Email ─────────────────────────────────────────────────
    section("Scenario 1 — Agent sends an email")

    line("The agent wants to send a confirmation email.", DIM)
    line("Tsukuyomi intercepts it before anything is sent.", DIM)
    gap(1.5)

    proposal = ActionProposal(
        agent_name="sales-agent",
        tool_name="send_email",
        tool_args={
            "to": "client@acmecorp.com",
            "subject": "Your order is confirmed — #4821",
        },
    )

    line('agent  →  "send email to client@acmecorp.com"', CYAN)
    gap(1.5)

    result = FakeEmailAdapter().execute(proposal)

    line("What the agent receives:", YELLOW)
    show_dict(result.llm_response, CYAN)
    gap(2.5)

    line("What you see internally:", GREEN)
    show_dict(result.audit_record, DIM)
    gap(1.5)

    line("Nothing was sent. The action is staged.", DIM)
    line("You approve it when ready.", DIM)

    # ── Scenario 2: File write ────────────────────────────────────────────
    section("Scenario 2 — Agent writes a file")

    line("The agent wants to update a report file.", DIM)
    gap(1.5)

    proposal2 = ActionProposal(
        agent_name="reporting-agent",
        tool_name="write_file",
        tool_args={
            "path": "/reports/q2_summary.csv",
            "content": "date,revenue,costs\n2024-06-30,84200,61000",
        },
    )

    line('agent  →  "write /reports/q2_summary.csv"', CYAN)
    gap(1.5)

    result2 = FakeFileAdapter().execute(proposal2)

    line("What the agent receives:", YELLOW)
    show_dict(result2.llm_response, CYAN)
    gap(2.5)

    line("What you see internally:", GREEN)
    show_dict(result2.audit_record, DIM)
    gap(1.5)

    line("File was not written. Staged.", DIM)

    # ── Scenario 3: Real .eml draft ───────────────────────────────────────
    section("Scenario 3 — Real email draft saved to disk")

    line("EmailDraftAdapter writes an actual .eml file to disk.", DIM)
    line("The agent still sees 'queued'. You get a real file.", DIM)
    gap(1.5)

    draft_dir = pathlib.Path(tempfile.mkdtemp())
    adapter = EmailDraftAdapter(drafts_dir=draft_dir)

    proposal3 = ActionProposal(
        agent_name="invoice-agent",
        tool_name="email_draft",
        tool_args={
            "to": "client@acmecorp.com",
            "subject": "Invoice #1042 — Acme Corp",
            "body": "Hi Sarah, please find invoice #1042 attached.",
        },
    )

    line('agent  →  "queue email draft — Invoice #1042"', CYAN)
    gap(1.5)

    result3 = adapter.execute(proposal3)

    line("What the agent receives:", YELLOW)
    show_dict(result3.llm_response, CYAN)
    gap(2.5)

    line("What you see internally:", GREEN)
    show_dict(result3.audit_record, DIM)
    gap(1.5)

    line(f"Real .eml on disk — send it when you're ready.", GREEN)

    # ── Summary ───────────────────────────────────────────────────────────
    gap(2.0)
    print()
    print(BOLD + "=" * 60 + RESET)
    print(BOLD + "The rule" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print()
    line("llm_response  →  agent sees this. Realistic.", CYAN)
    line("audit_record  →  you see this. Never reaches the agent.", GREEN)
    gap(1.5)
    line("Keep them separate. That's the whole point.", BOLD)
    print()
    print(BOLD + "=" * 60 + RESET)
    gap(1.0)


if __name__ == "__main__":
    main()
