from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ActionProposal(BaseModel):
    """
    A proposed action from an AI agent.

    This is the only input Tsukuyomi needs to simulate an action.
    No framework dependencies — fully standalone.
    """

    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    client: str = ""
