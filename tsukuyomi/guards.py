from __future__ import annotations

"""
Tsukuyomi guards — always active, no LLM required.

Three guards run before every action enters the genjutsu:

1. BlocklistGuard  — hardcoded destructive pattern matching. Instant. No LLM.
2. LoopDetector    — sliding window. Stops infinite repetition before it costs money.
3. BudgetGuard     — daily spend cap. Hard stop when limit is hit.

These are architectural enforcement, not prompt suggestions.
An agent cannot talk its way past them.
"""

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from typing import Optional

# Patterns that are always blocked — no exceptions, no LLM
_BLOCKLIST = [
    r"rm\s+-rf\s+[/~]",
    r"dd\s+if=.*of=/dev/(sd|hd|nvme|disk)",
    r"\bDROP\s+TABLE\b(?!.*\bWHERE\b)",
    r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)",
    r"git\s+(push|reset).*--(force|hard)",
    r":\(\)\s*\{.*:\|:&\s*\};:",
    r"(curl|wget)\s+.*\|\s*(bash|sh|zsh)",
    r"\b(shutdown|reboot)\b.*(-h|-r|now)",
    r"mkfs\.\w+",
    r">\s*/dev/(sd|hd|nvme|zero|null)\b",
    r"chmod\s+-R\s+777\s+/",
    r"format\s+[a-zA-Z]:",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _BLOCKLIST]


class BlocklistGuard:
    """
    Hardcoded blocklist. No LLM. Always active. O(n) regex matching.
    Returns the matched pattern string if blocked, None if clean.
    """

    def check(self, text: str) -> Optional[str]:
        for pattern in _COMPILED:
            if pattern.search(text):
                return pattern.pattern
        return None


class LoopDetector:
    """
    Sliding window loop detection.

    Tracks action keys over the last window_seconds seconds.
    If the same action repeats more than max_repeats times → loop detected.

    action_key = tool_name + hash(args) — stable, not user-controlled.
    """

    def __init__(self, window_seconds: int = 60, max_repeats: int = 3) -> None:
        self._window = window_seconds
        self._max = max_repeats
        self._history: list[tuple[float, str]] = []

    def record(self, action_key: str) -> bool:
        """
        Record an action. Returns True if a loop is detected.
        Call this BEFORE executing the action.
        """
        now = time.monotonic()
        cutoff = now - self._window
        self._history = [(t, k) for t, k in self._history if t >= cutoff]
        self._history.append((now, action_key))
        count = sum(1 for _, k in self._history if k == action_key)
        return count > self._max

    @staticmethod
    def make_key(tool_name: str, tool_args: dict) -> str:
        args_hash = hashlib.sha256(
            json.dumps(tool_args, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
        return f"{tool_name}:{args_hash}"


class BudgetGuard:
    """
    Daily cost cap. Hard stop when the limit is reached.
    Resets at midnight UTC.

    Cost tracking is approximate — callers report spend via record().
    When no cost data is available, use token counts as a proxy.
    """

    def __init__(self, daily_limit_usd: float = 5.0) -> None:
        self._limit = daily_limit_usd
        self._spent = 0.0
        self._reset_date = datetime.now(timezone.utc).date()

    def _check_reset(self) -> None:
        today = datetime.now(timezone.utc).date()
        if today > self._reset_date:
            self._spent = 0.0
            self._reset_date = today

    def record(self, cost_usd: float) -> None:
        self._check_reset()
        self._spent += cost_usd

    def is_over(self) -> bool:
        self._check_reset()
        return self._spent >= self._limit

    @property
    def spent(self) -> float:
        self._check_reset()
        return self._spent

    @property
    def remaining(self) -> float:
        self._check_reset()
        return max(0.0, self._limit - self._spent)
