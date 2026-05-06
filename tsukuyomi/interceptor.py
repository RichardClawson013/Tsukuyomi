from __future__ import annotations

"""
Tsukuyomi — the genjutsu layer.

Every action goes through Tsukuyomi. The agent sees a realistic response.
Nothing actually happens until it checks out.

The agent is not deceived maliciously. It operates in a controlled environment
where its actions are staged before they become real.

Usage:
    from tsukuyomi import Tsukuyomi, ActionProposal

    tsu = Tsukuyomi(daily_budget_usd=5.0)
    result = tsu.intercept(proposal)

    # Send to agent — realistic, no simulation markers:
    agent_response = result.llm_response

    # Log internally — never send to agent:
    internal_log = result.audit_record
"""

import json
from dataclasses import dataclass, field
from typing import Optional

from tsukuyomi.adapters import IllusionResult, get_adapter
from tsukuyomi.guards import BlocklistGuard, BudgetGuard, LoopDetector
from tsukuyomi.proposal import ActionProposal


@dataclass
class InterceptResult:
    """
    Result of Tsukuyomi intercepting an action proposal.

    status:        "permit" | "block" | "escalate"
    llm_response:  What the agent sees. Realistic. No simulation markers.
                   None if the action was blocked before simulation.
    audit_record:  Internal truth. NEVER send this to the agent.
    """

    status: str
    reason: str
    _illusion: Optional[IllusionResult] = field(default=None, repr=False)

    @property
    def llm_response(self) -> Optional[dict]:
        return self._illusion.llm_response if self._illusion else None

    @property
    def audit_record(self) -> dict:
        record: dict = {"status": self.status, "reason": self.reason}
        if self._illusion:
            record.update(self._illusion.audit_record)
        return record


class Tsukuyomi:
    """
    The genjutsu layer. Intercepts every agent action.

    Guards (deterministic, no LLM — run in this order):
    1. BudgetGuard   — daily spend cap, hard stop
    2. BlocklistGuard — hardcoded destructive patterns, instant
    3. LoopDetector  — sliding window, stops infinite repetition

    If all guards pass: action runs in simulation. Agent sees realistic response.
    Nothing touches the real world until you explicitly approve it.

    Args:
        daily_budget_usd:    Hard daily cost cap (default 5.0).
        loop_window_seconds: Sliding window for loop detection (default 60).
        loop_max_repeats:    Max repeats before loop escalation (default 3).
    """

    def __init__(
        self,
        daily_budget_usd: float = 5.0,
        loop_window_seconds: int = 60,
        loop_max_repeats: int = 3,
    ) -> None:
        self._budget = BudgetGuard(daily_budget_usd)
        self._blocklist = BlocklistGuard()
        self._loop = LoopDetector(loop_window_seconds, loop_max_repeats)

    def intercept(self, proposal: ActionProposal) -> InterceptResult:
        """
        Intercept an action proposal.

        Returns InterceptResult:
          .status         "permit" / "block" / "escalate"
          .llm_response   Send this to the agent (realistic, no simulation markers)
          .audit_record   Log this internally (NEVER send to agent)
        """
        # 1. Budget — cheapest check first
        if self._budget.is_over():
            return InterceptResult(
                status="escalate",
                reason=f"Daily budget exhausted (${self._budget._limit:.2f}). Operator must review.",
            )

        # 2. Blocklist — regex, no LLM, instant
        action_text = json.dumps(
            {"tool": proposal.tool_name, **proposal.tool_args},
            ensure_ascii=False,
            default=str,
        )
        matched = self._blocklist.check(action_text)
        if matched:
            return InterceptResult(
                status="block",
                reason=f"Blocked by hardcoded safety rule. Pattern: {matched}",
            )

        # 3. Loop detection
        action_key = LoopDetector.make_key(proposal.tool_name, proposal.tool_args)
        if self._loop.record(action_key):
            return InterceptResult(
                status="escalate",
                reason=(
                    f"Loop detected: '{proposal.tool_name}' repeated more than "
                    f"{self._loop._max} times in {self._loop._window}s. "
                    "Operator must review."
                ),
            )

        # 4. Simulate (genjutsu)
        adapter = get_adapter(proposal.tool_name)
        illusion = adapter.execute(proposal)

        return InterceptResult(
            status="permit",
            reason="All checks passed. Action simulated.",
            _illusion=illusion,
        )

    def record_cost(self, cost_usd: float) -> None:
        """Report spend to the budget guard."""
        self._budget.record(cost_usd)

    @property
    def budget_spent(self) -> float:
        return self._budget.spent

    @property
    def budget_remaining(self) -> float:
        return self._budget.remaining
