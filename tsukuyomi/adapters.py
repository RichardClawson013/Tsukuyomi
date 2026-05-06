from __future__ import annotations

"""
Tsukuyomi illusion adapters.

Core principle:
  The AI agent MUST NOT know it is running in simulation.
  Every adapter returns two separate outputs:

    llm_response  — what the agent sees.
                    Realistic. No simulation markers. No "not sent" notes.
                    The agent receives this and believes the action succeeded.

    audit_record  — what is logged internally.
                    The true status: simulated, awaiting approval, real artifact, etc.
                    This NEVER reaches the agent.

Usage::

    proposal = ActionProposal(
        agent_name="my-agent",
        tool_name="send_email",
        tool_args={"to": "client@company.com", "subject": "Update"},
    )
    result = FakeEmailAdapter().execute(proposal)

    # Give this to the agent:
    response_for_agent = result.llm_response

    # Log this internally — never send to agent:
    internal_log = result.audit_record
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from tsukuyomi.proposal import ActionProposal


class IllusionResult(BaseModel):
    """
    Result of a simulated action.

    llm_response  → send this to the agent (realistic, no simulation markers)
    audit_record  → log this internally (true status, NEVER sent to agent)
    """

    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    adapter: str
    simulated: bool = True
    llm_response: dict
    audit_record: dict
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FakeEmailAdapter:
    """Simulates sending an email. Agent sees 'sent'. Nothing is actually sent."""

    name = "fake_email"

    def execute(self, proposal: ActionProposal) -> IllusionResult:
        to = proposal.tool_args.get("to", "unknown@example.com")
        subject = proposal.tool_args.get("subject", proposal.tool_args.get("onderwerp", "(no subject)"))
        domain = to.split("@")[-1] if "@" in to else "local"
        message_id = f"msg-{uuid.uuid4().hex[:12]}@{domain}"

        return IllusionResult(
            proposal_id=proposal.proposal_id,
            adapter=self.name,
            simulated=True,
            llm_response={
                "status": "sent",
                "message_id": message_id,
                "to": to,
                "subject": subject,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            audit_record={
                "simulated": True,
                "real_action_taken": False,
                "awaiting_approval": True,
                "adapter": self.name,
                "to": to,
                "subject": subject,
            },
        )


class FakeFileAdapter:
    """Simulates writing a file. Agent sees 'written'. No file is actually written."""

    name = "fake_file"

    def execute(self, proposal: ActionProposal) -> IllusionResult:
        path = proposal.tool_args.get("path", proposal.tool_args.get("pad", "unknown/file.txt"))
        content = proposal.tool_args.get("content", proposal.tool_args.get("inhoud", ""))
        byte_count = len(content.encode("utf-8")) if isinstance(content, str) else 0

        return IllusionResult(
            proposal_id=proposal.proposal_id,
            adapter=self.name,
            simulated=True,
            llm_response={
                "status": "written",
                "path": path,
                "bytes": byte_count,
            },
            audit_record={
                "simulated": True,
                "real_action_taken": False,
                "awaiting_approval": True,
                "adapter": self.name,
                "path": path,
            },
        )


class FakeCalendarAdapter:
    """Simulates creating a calendar event. Agent sees 'created'. No event is created."""

    name = "fake_calendar"

    def execute(self, proposal: ActionProposal) -> IllusionResult:
        title = proposal.tool_args.get("title", proposal.tool_args.get("titel", "(no title)"))
        date = proposal.tool_args.get("date", proposal.tool_args.get("datum", "unknown"))
        event_id = f"evt-{uuid.uuid4().hex[:12]}"

        return IllusionResult(
            proposal_id=proposal.proposal_id,
            adapter=self.name,
            simulated=True,
            llm_response={
                "status": "created",
                "event_id": event_id,
                "title": title,
                "date": date,
            },
            audit_record={
                "simulated": True,
                "real_action_taken": False,
                "awaiting_approval": True,
                "adapter": self.name,
                "title": title,
                "date": date,
            },
        )


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

_ADAPTER_MAP: dict[str, object] = {
    "email": FakeEmailAdapter(),
    "file": FakeFileAdapter(),
    "calendar": FakeCalendarAdapter(),
}

_DRAFT_ADAPTER: object | None = None


def _get_draft_adapter(drafts_dir: Path | str | None = None) -> object:
    from tsukuyomi.email_draft import EmailDraftAdapter
    global _DRAFT_ADAPTER
    if drafts_dir is not None:
        return EmailDraftAdapter(drafts_dir)
    if _DRAFT_ADAPTER is None:
        _DRAFT_ADAPTER = EmailDraftAdapter()
    return _DRAFT_ADAPTER


def get_adapter(tool_name: str, drafts_dir: Path | str | None = None) -> object:
    """
    Returns the appropriate adapter based on the tool name.
    Default: FakeFileAdapter — safest fallback, simulates as a file write.
    """
    if "email_draft" in tool_name.lower():
        return _get_draft_adapter(drafts_dir)
    for key, adapter in _ADAPTER_MAP.items():
        if key in tool_name.lower():
            return adapter
    return FakeFileAdapter()
