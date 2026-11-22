# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Keeps avenir-mcp well within YNAB's rolling-hour request limit."""

from __future__ import annotations

import math
import time
from collections import deque


class Pace:
    """Keeps avenir-mcp well within YNAB's limit: 200 requests per hour and per token.

    YNAB counts over a rolling hour and, once the limit is reached, answers 429. That
    answer is never retried: no request leaves for as long as its `Retry-After` asks,
    or for ten minutes when it asks for nothing. And avenir-mcp stops by itself at 180
    requests in the hour, leaving the rest to other apps using the same token. A retry
    of a failed request counts here like any other, so nothing escapes the budget.
    """

    budget = 180
    """Requests sent in the last hour beyond which avenir-mcp waits; YNAB allows 200."""
    pause = 600.0
    """Seconds without any request after a 429 that named no delay of its own."""
    hour = 3600.0

    def __init__(self) -> None:
        """Start with no request sent and no pause."""
        self.sent: deque[float] = deque()
        self.paused_until = 0.0

    def reset(self) -> None:
        """Forget the requests sent and any pause."""
        self.sent.clear()
        self.paused_until = 0.0

    def take(self) -> None:
        """Count a request about to leave, or refuse it before it reaches YNAB.

        Raises:
            RuntimeError: While paused after a 429, or when the hour's budget is spent.
        """
        now = time.monotonic()
        if now < self.paused_until:
            raise RuntimeError(
                "YNAB's limit of 200 requests per hour was reached. Nothing was sent: "
                f"avenir-mcp calls YNAB again in {_minutes(self.paused_until - now)}. "
                "Tell the user; do not retry before then."
            )
        while self.sent and now - self.sent[0] >= self.hour:
            self.sent.popleft()
        if len(self.sent) >= self.budget:
            raise RuntimeError(
                f"avenir-mcp sent {len(self.sent)} requests to YNAB in the last hour, close "
                "to YNAB's limit of 200 per hour. Nothing was sent: the next request can "
                f"leave in {_minutes(self.sent[0] + self.hour - now)}. Tell the user; do not "
                "retry before then."
            )
        self.sent.append(now)

    def refused(self, seconds: float | None = None) -> float:
        """Pause every request after YNAB answered 429.

        Args:
            seconds: What YNAB's Retry-After asked for, or None when it asked nothing.

        Returns:
            The seconds no request leaves for.
        """
        held = self.pause if seconds is None else seconds
        self.paused_until = time.monotonic() + held
        return held


def _minutes(seconds: float) -> str:
    """Say a wait in whole minutes, rounded up.

    Args:
        seconds: The wait.

    Returns:
        E.g. "1 minute" or "10 minutes".
    """
    count = max(1, math.ceil(seconds / 60))
    return f"{count} minute" + ("s" if count > 1 else "")


PACE = Pace()
