"""
examples/demo_run.py — Scripted demo for Tsukuyomi.

Shows the full illusion in action:
  - The agent proposes an action
  - Tsukuyomi intercepts it
  - The agent receives a realistic response (believes it succeeded)
  - You see the internal audit record (the truth)

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
RED    = "\033[31m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

SEP = BOLD + "─" * 60 + RESET


def pause(n: float = 0.15) -> None:
    time.sleep(n)


def show(text: str, color: str = "", indent: int = 0) -> None:
    prefix = "  " * indent
    print(color + prefix + text + RESET, flush=True)
    pause()


def section(title: str) -> None:
    print()
    print(SEP)
    show(title, BOLD)
    print(SEP)
    pause(0.1)


def agent_says(text: str) -> None:
    show(f"agent  →  {text}", CYAN)
    pause(0.05)


def you_see(label: str, data: dict) -> None:
    import json
    show(f"you    ←  {label}:", GREEN)
    for line in json.dumps(data, indent=2).splitlines():
        show(line, DIM, indent=2)
    pause(0.05)


def agent_receives(data: dict) -> None:
    import json
    show("agent  ←  (Tsukuyomi hands back)", YELLOW)
    for line in json.dumps(data, indent=2).splitlines():
        show(line, CYAN, indent=2)
    pause(0.05)


def main() -> None:
    print()
    print(BOLD + "=" * 60 + RESET)
    print(BOLD + "Tsukuyomi — Illusion Layer Demo" + RESET)
    print(BOLD + "=" * 60 + RESET)
    show("The agent acts. You decide when it's real.", DIM)
    pause(0.2)

    # ── Scenario 1: Email ─────────────────────────────────────────────────
    section("Scenario 1 — Agent sends an email")

    show("The agent wants to send a confirmation email to the client.", DIM)
    show("Tsukuyomi intercepts it.", DIM)
    print()
    pause(0.1)

    proposal = ActionProposal(
        agent_name="sales-agent",
        tool_name="send_email",
        tool_args={
            "to": "client@acmecorp.com",
            "subject": "Your order is confirmed — #4821",
            "body": "Hi Sarah, your order has been confirmed and is now in production.",
        },
    )

    agent_says('"send email to client@acmecorp.com — order confirmed"')
    pause(0.1)

    result = FakeEmailAdapter().execute(proposal)

    agent_receives(result.llm_response)
    print()
    show("The agent believes the email was sent. It moves on.", DIM)
    print()
    pause(0.1)

    you_see("audit record (internal — never reaches the agent)", result.audit_record)
    show("Nothing was sent. The action is staged. You approve it when ready.", DIM)

    # ── Scenario 2: File write ────────────────────────────────────────────
    section("Scenario 2 — Agent writes a file")

    show("The agent wants to update a report file.", DIM)
    print()
    pause(0.1)

    proposal2 = ActionProposal(
        agent_name="reporting-agent",
        tool_name="write_file",
        tool_args={
            "path": "/reports/q2_summary.csv",
            "content": "date,revenue,costs\n2024-06-30,84200,61000",
        },
    )

    agent_says('"write file /reports/q2_summary.csv"')
    pause(0.1)

    result2 = FakeFileAdapter().execute(proposal2)

    agent_receives(result2.llm_response)
    print()
    you_see("audit record", result2.audit_record)
    show("File was not written. Staged.", DIM)

    # ── Scenario 3: Calendar ──────────────────────────────────────────────
    section("Scenario 3 — Agent books a meeting")

    show("The agent wants to schedule a follow-up call.", DIM)
    print()
    pause(0.1)

    proposal3 = ActionProposal(
        agent_name="calendar-agent",
        tool_name="create_calendar_event",
        tool_args={
            "title": "Follow-up call — Acme Corp",
            "date": "2024-07-15",
            "time": "14:00",
            "attendees": ["rob@droogdoc.nl", "sarah@acmecorp.com"],
        },
    )

    agent_says('"create calendar event — follow-up call 2024-07-15 14:00"')
    pause(0.1)

    result3 = FakeCalendarAdapter().execute(proposal3)

    agent_receives(result3.llm_response)
    print()
    you_see("audit record", result3.audit_record)
    show("No event created. Staged.", DIM)

    # ── Scenario 4: Real .eml draft ───────────────────────────────────────
    section("Scenario 4 — Real email draft saved to disk")

    show("EmailDraftAdapter writes an actual .eml file.", DIM)
    show("Agent still sees 'queued'. You get a real file you can send.", DIM)
    print()
    pause(0.1)

    draft_dir = pathlib.Path(tempfile.mkdtemp())
    adapter = EmailDraftAdapter(drafts_dir=draft_dir)

    proposal4 = ActionProposal(
        agent_name="invoice-agent",
        tool_name="email_draft",
        tool_args={
            "to": "client@acmecorp.com",
            "subject": "Invoice #1042 — Acme Corp",
            "body": "Hi Sarah,\n\nPlease find invoice #1042 attached.\n\nBest,\nRob",
        },
    )

    agent_says('"queue email draft — Invoice #1042"')
    pause(0.1)

    result4 = adapter.execute(proposal4)

    agent_receives(result4.llm_response)
    print()
    you_see("audit record", result4.audit_record)
    show(f"Real .eml file on disk: {result4.audit_record['draft_path']}", GREEN)
    show("Send it whenever you're ready. Or don't.", DIM)

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print(BOLD + "=" * 60 + RESET)
    print(BOLD + "The rule" + RESET)
    print(BOLD + "=" * 60 + RESET)
    print()
    show("llm_response  →  agent sees this. Realistic. No simulation markers.", CYAN)
    show("audit_record  →  you see this. True status. Never reaches the agent.", GREEN)
    print()
    show("Keep them separate. That's the whole point.", BOLD)
    print()
    print(BOLD + "=" * 60 + RESET)
    print()


if __name__ == "__main__":
    main()
