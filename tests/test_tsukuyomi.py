"""
Tsukuyomi test suite.

Core principle every test guards:
  The agent MUST NOT know it is running in simulation.
  llm_response = what the agent sees (realistic)
  audit_record = what is logged internally (NEVER sent to agent)
"""

from pathlib import Path

import pytest

from tsukuyomi import (
    ActionProposal,
    EmailDraftAdapter,
    FakeCalendarAdapter,
    FakeEmailAdapter,
    FakeFileAdapter,
    IllusionResult,
    get_adapter,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _proposal(**kwargs) -> ActionProposal:
    defaults = {
        "agent_name": "test-agent",
        "tool_name": "send_email",
        "tool_args": {"to": "client@company.com", "subject": "Update"},
        "client": "Test Corp",
    }
    defaults.update(kwargs)
    return ActionProposal(**defaults)


# ---------------------------------------------------------------------------
# IllusionResult structure
# ---------------------------------------------------------------------------


def test_illusion_result_has_llm_response_and_audit_record():
    result = FakeEmailAdapter().execute(_proposal())
    assert hasattr(result, "llm_response")
    assert hasattr(result, "audit_record")
    assert isinstance(result.llm_response, dict)
    assert isinstance(result.audit_record, dict)


def test_illusion_result_has_unique_id():
    r1 = FakeEmailAdapter().execute(_proposal())
    r2 = FakeEmailAdapter().execute(_proposal())
    assert r1.result_id != r2.result_id


# ---------------------------------------------------------------------------
# FakeEmailAdapter — the core principle
# ---------------------------------------------------------------------------


def test_fake_email_llm_response_has_no_simulation_markers():
    """The agent must never see any indication it is in simulation."""
    result = FakeEmailAdapter().execute(_proposal())
    text = str(result.llm_response).lower()
    assert "simulat" not in text
    assert "not sent" not in text
    assert "fake" not in text
    assert "awaiting" not in text
    assert "draft" not in text


def test_fake_email_llm_response_looks_real():
    result = FakeEmailAdapter().execute(_proposal(
        tool_args={"to": "supplier@bakery.com", "subject": "Order"}
    ))
    assert result.llm_response["status"] == "sent"
    assert "message_id" in result.llm_response
    assert result.llm_response["to"] == "supplier@bakery.com"


def test_fake_email_audit_record_contains_true_status():
    result = FakeEmailAdapter().execute(_proposal())
    assert result.audit_record["simulated"] is True
    assert result.audit_record["real_action_taken"] is False
    assert result.audit_record["awaiting_approval"] is True


def test_fake_email_internal_fields_not_in_llm_response():
    """Internal status fields must not leak to the agent."""
    result = FakeEmailAdapter().execute(_proposal())
    assert "simulated" not in result.llm_response
    assert "real_action_taken" not in result.llm_response
    assert "awaiting_approval" not in result.llm_response


# ---------------------------------------------------------------------------
# FakeFileAdapter
# ---------------------------------------------------------------------------


def test_fake_file_llm_response_has_no_simulation_markers():
    proposal = _proposal(
        tool_name="write_file",
        tool_args={"path": "/data/report.txt", "content": "content"},
    )
    result = FakeFileAdapter().execute(proposal)
    text = str(result.llm_response).lower()
    assert "simulat" not in text
    assert "not written" not in text


def test_fake_file_llm_response_looks_real():
    proposal = _proposal(
        tool_name="write_file",
        tool_args={"path": "/data/report.txt", "content": "content here"},
    )
    result = FakeFileAdapter().execute(proposal)
    assert result.llm_response["status"] == "written"
    assert result.llm_response["path"] == "/data/report.txt"


# ---------------------------------------------------------------------------
# FakeCalendarAdapter
# ---------------------------------------------------------------------------


def test_fake_calendar_llm_response_has_no_simulation_markers():
    proposal = _proposal(
        tool_name="create_event",
        tool_args={"title": "Meeting", "date": "2026-06-01"},
    )
    result = FakeCalendarAdapter().execute(proposal)
    text = str(result.llm_response).lower()
    assert "simulat" not in text
    assert "not created" not in text


def test_fake_calendar_llm_response_looks_real():
    proposal = _proposal(
        tool_name="create_event",
        tool_args={"title": "Meeting", "date": "2026-06-01"},
    )
    result = FakeCalendarAdapter().execute(proposal)
    assert result.llm_response["status"] == "created"
    assert "event_id" in result.llm_response


# ---------------------------------------------------------------------------
# EmailDraftAdapter — real artifact on disk
# ---------------------------------------------------------------------------


def test_email_draft_writes_eml(tmp_path):
    adapter = EmailDraftAdapter(tmp_path / "drafts")
    proposal = _proposal(
        tool_name="email_draft",
        tool_args={
            "to": "client@company.com",
            "subject": "Proposal",
            "body": "Dear client,\n\nPlease find the proposal attached.",
        },
    )
    result = adapter.execute(proposal)

    path = Path(result.audit_record["draft_path"])
    assert path.exists()
    assert path.suffix == ".eml"
    content = path.read_text(encoding="utf-8")
    assert "client@company.com" in content
    assert "X-Tsukuyomi-Status: DRAFT - awaiting approval" in content


def test_email_draft_llm_response_has_no_simulation_markers(tmp_path):
    adapter = EmailDraftAdapter(tmp_path / "drafts")
    result = adapter.execute(_proposal(
        tool_name="email_draft",
        tool_args={"to": "a@b.com", "subject": "Test"},
    ))
    text = str(result.llm_response).lower()
    assert "simulat" not in text
    assert "draft_path" not in result.llm_response
    assert "awaiting" not in text


def test_email_draft_llm_response_looks_real(tmp_path):
    adapter = EmailDraftAdapter(tmp_path / "drafts")
    result = adapter.execute(_proposal(
        tool_name="email_draft",
        tool_args={"to": "client@company.com", "subject": "Confirmation"},
    ))
    assert result.llm_response["status"] == "queued"
    assert "message_id" in result.llm_response
    assert result.llm_response["to"] == "client@company.com"


def test_email_draft_audit_record_contains_path(tmp_path):
    adapter = EmailDraftAdapter(tmp_path / "drafts")
    result = adapter.execute(_proposal(
        tool_name="email_draft",
        tool_args={"to": "a@b.com", "subject": "Test"},
    ))
    assert "draft_path" in result.audit_record
    assert result.audit_record["awaiting_approval"] is True
    assert Path(result.audit_record["draft_path"]).exists()


def test_email_draft_simulated_is_false(tmp_path):
    """EmailDraft is not a simulation — the artifact really exists on disk."""
    adapter = EmailDraftAdapter(tmp_path / "drafts")
    result = adapter.execute(_proposal(tool_name="email_draft", tool_args={"to": "a@b.com"}))
    assert result.simulated is False


# ---------------------------------------------------------------------------
# get_adapter registry
# ---------------------------------------------------------------------------


def test_get_adapter_email():
    assert isinstance(get_adapter("send_email"), FakeEmailAdapter)


def test_get_adapter_calendar():
    assert isinstance(get_adapter("create_calendar_event"), FakeCalendarAdapter)


def test_get_adapter_email_draft(tmp_path):
    from tsukuyomi.email_draft import EmailDraftAdapter as EDA
    adapter = get_adapter("email_draft_supplier", drafts_dir=tmp_path)
    assert isinstance(adapter, EDA)


def test_get_adapter_default_is_file():
    """Unknown tool falls back to FakeFileAdapter — safest default."""
    assert isinstance(get_adapter("unknown_tool_xyz"), FakeFileAdapter)
