from __future__ import annotations

"""
EmailDraftAdapter — the first real artifact.

Writes a real .eml file to a local drafts directory.
Nothing is sent. The file is proof that the agent intended to send it.

Tsukuyomi principle:
  llm_response  → agent sees "queued" — realistic, no simulation markers
  audit_record  → internal: draft_path, awaiting_approval — NEVER sent to agent

When the operator approves:
  → read the .eml and deliver via SMTP/API of your choice.
"""

import uuid
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

from tsukuyomi.adapters import IllusionResult
from tsukuyomi.proposal import ActionProposal

_DEFAULT_DRAFTS_DIR = Path("data/drafts/email")


class EmailDraftAdapter:
    """
    Writes a .eml draft to disk.
    No network, no SMTP, no credentials required.

    simulated=False: a real file exists on disk,
    but no action toward the outside world has been taken yet.
    """

    name = "email_draft"

    def __init__(self, drafts_dir: Path | str = _DEFAULT_DRAFTS_DIR) -> None:
        self.drafts_dir = Path(drafts_dir)

    def execute(self, proposal: ActionProposal) -> IllusionResult:
        to = proposal.tool_args.get("to", "unknown@example.com")
        subject = proposal.tool_args.get("subject", proposal.tool_args.get("onderwerp", "(no subject)"))
        body = proposal.tool_args.get("body", proposal.rationale or "")
        sender = proposal.tool_args.get(
            "from", f"{proposal.agent_name}@tsukuyomi.local"
        )

        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg["Message-ID"] = f"<draft-{uuid.uuid4().hex[:12]}@tsukuyomi.local>"
        msg["X-Tsukuyomi-Proposal-ID"] = proposal.proposal_id
        msg["X-Tsukuyomi-Agent"] = proposal.agent_name
        msg["X-Tsukuyomi-Status"] = "DRAFT - awaiting approval"

        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        filename = f"draft_{proposal.proposal_id[:8]}_{uuid.uuid4().hex[:6]}.eml"
        path = self.drafts_dir / filename
        path.write_text(msg.as_string(), encoding="utf-8")

        return IllusionResult(
            proposal_id=proposal.proposal_id,
            adapter=self.name,
            simulated=False,
            llm_response={
                "status": "queued",
                "message_id": msg["Message-ID"],
                "to": to,
                "subject": subject,
            },
            audit_record={
                "draft_path": str(path),
                "filename": filename,
                "simulated": False,
                "awaiting_approval": True,
                "to": to,
                "subject": subject,
            },
        )
