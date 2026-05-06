"""
Tsukuyomi — genjutsu layer for AI agents.

Every action goes through Tsukuyomi. The agent sees a realistic response.
Nothing actually happens until it checks out.

    from tsukuyomi import Tsukuyomi, ActionProposal
"""

from tsukuyomi.adapters import (
    FakeCalendarAdapter,
    FakeEmailAdapter,
    FakeFileAdapter,
    IllusionResult,
    get_adapter,
)
from tsukuyomi.email_draft import EmailDraftAdapter
from tsukuyomi.interceptor import InterceptResult, Tsukuyomi
from tsukuyomi.proposal import ActionProposal

__all__ = [
    "Tsukuyomi",
    "InterceptResult",
    "ActionProposal",
    "IllusionResult",
    "FakeEmailAdapter",
    "FakeFileAdapter",
    "FakeCalendarAdapter",
    "EmailDraftAdapter",
    "get_adapter",
]

__version__ = "0.1.0"
