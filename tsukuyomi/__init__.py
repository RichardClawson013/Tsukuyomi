"""
Tsukuyomi — illusion layer for AI agents.

The agent never knows it's not in the real world.

  from tsukuyomi import ActionProposal, FakeEmailAdapter, get_adapter, IllusionResult
"""

from tsukuyomi.adapters import (
    FakeCalendarAdapter,
    FakeEmailAdapter,
    FakeFileAdapter,
    IllusionResult,
    get_adapter,
)
from tsukuyomi.email_draft import EmailDraftAdapter
from tsukuyomi.proposal import ActionProposal

__all__ = [
    "ActionProposal",
    "IllusionResult",
    "FakeEmailAdapter",
    "FakeFileAdapter",
    "FakeCalendarAdapter",
    "EmailDraftAdapter",
    "get_adapter",
]

__version__ = "0.1.0"
