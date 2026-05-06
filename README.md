# Tsukuyomi

[![CI](https://github.com/RichardClawson013/Tsukuyomi/actions/workflows/ci.yml/badge.svg)](https://github.com/RichardClawson013/Tsukuyomi/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tsukuyomi)](https://pypi.org/project/tsukuyomi/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/tsukuyomi)](https://pypi.org/project/tsukuyomi/)

> **Your AI agent acts. You decide when it's real.**

---

![Tsukuyomi demo](docs/media/demo.gif)

---

## The problem

You give an AI agent access to your email, your files, your calendar. It does its job. Then one day it sends a message you weren't ready to send. Moves a file you needed. Books a meeting during a holiday.

The agent didn't malfunction. It did exactly what you asked — just at the wrong moment, to the wrong person, without you seeing it first.

The standard fix is more prompting. "Be careful." "Always ask first." That works until it doesn't. Prompts are suggestions. The agent can still act, and eventually it will.

**Tsukuyomi intercepts every action before it reaches the outside world.** The agent believes it succeeded. The action waits for your approval. You decide when — and whether — it becomes real.

---

## How it works

Every tool call the agent makes goes through Tsukuyomi first.

The agent gets back a realistic response: the email was sent, the file was written, the meeting was created. It continues normally. It has no idea nothing happened yet.

Behind the scenes, Tsukuyomi logged the real status: simulated, not executed, waiting for approval. That log is yours.

```
Agent  →  "send email to client"
           ↓
        Tsukuyomi
           ↓ intercepts
           ↓ returns realistic response to agent
           ↓ logs true status internally
           ↓
Agent  ←  {"status": "sent", "message_id": "msg-a1b2c3@company.com"}
           (agent believes it. nothing was actually sent.)

You    ←  audit_record: {"simulated": True, "awaiting_approval": True, "to": "client@..."}
           (you decide: approve → send for real. reject → nothing happens.)
```

This separation — what the agent sees vs. what actually happened — is the whole idea. The agent is not lied to maliciously. It simply operates in a controlled environment where its actions are staged before they're real.

---

## Install

```bash
pip install tsukuyomi
```

Requires Python 3.11+. No external services. No API keys. Runs entirely local.

---

## Demo

Copy this. Run it. It works with no configuration.

```python
from tsukuyomi import ActionProposal, FakeEmailAdapter, EmailDraftAdapter

# --- Scenario 1: simulate an email ---
proposal = ActionProposal(
    agent_name="my-agent",
    tool_name="send_email",
    tool_args={
        "to": "client@company.com",
        "subject": "Your order is confirmed",
    },
)

result = FakeEmailAdapter().execute(proposal)

print("Agent sees:")
print(result.llm_response)
# {'status': 'sent', 'message_id': 'msg-4f8a1c2d9b3e@company.com',
#  'to': 'client@company.com', 'subject': 'Your order is confirmed', ...}

print("\nYou see:")
print(result.audit_record)
# {'simulated': True, 'real_action_taken': False, 'awaiting_approval': True,
#  'to': 'client@company.com', 'subject': 'Your order is confirmed'}
```

```python
# --- Scenario 2: write a real .eml draft to disk ---
import tempfile, pathlib

draft_dir = pathlib.Path(tempfile.mkdtemp())
adapter = EmailDraftAdapter(drafts_dir=draft_dir)

proposal = ActionProposal(
    agent_name="my-agent",
    tool_name="email_draft",
    tool_args={
        "to": "client@company.com",
        "subject": "Invoice #1042",
        "body": "Hi, please find your invoice attached.",
    },
)

result = adapter.execute(proposal)

print("Agent sees:", result.llm_response["status"])   # queued
print("Draft on disk:", result.audit_record["draft_path"])
# /tmp/.../draft_a3b2c1d4_f8e9.eml  ← real file, ready to send when you say so
```

---

## Adapters

| Adapter | What the agent sees | What actually happens |
|---|---|---|
| `FakeEmailAdapter` | `{"status": "sent", ...}` | Nothing. No email sent. |
| `FakeFileAdapter` | `{"status": "written", ...}` | Nothing. No file written. |
| `FakeCalendarAdapter` | `{"status": "created", ...}` | Nothing. No event created. |
| `EmailDraftAdapter` | `{"status": "queued", ...}` | Real `.eml` file saved to disk. |

Need a custom adapter? Subclass any of the above and implement `execute()`. Return an `IllusionResult` with `llm_response` and `audit_record`. That's the whole contract.

---

## The rule

One rule. No exceptions.

**`llm_response` goes to the agent. `audit_record` stays with you.**

If you accidentally send `audit_record` to the agent, the illusion breaks. The agent knows it's in a sandbox. It may behave differently. Keep them separate.

---

## Run the tests

```bash
git clone https://github.com/RichardClawson013/Tsukuyomi
cd Tsukuyomi
pip install -e ".[dev]"
pytest
```

19 tests. All green.

---

*Apache 2.0 — Rob de Vet*
