"""Text written by banks, merchants and anyone who can pay you, made safe to show.

Payee names and memos are untrusted. Shown as they are, a line break could add a
forged line to a confirmation question, and a right-to-left override or a
zero-width character could make one name look like another.
"""

from __future__ import annotations

import unicodedata

MAX_TEXT = 80

MAX_PAYEE = 200
"""YNAB refuses a payee_name longer than this."""
MAX_MEMO = 500
"""YNAB refuses a memo longer than this."""

# Control characters, line and paragraph separators: shown as a space.
_BREAKS = {"Cc", "Zl", "Zp"}
# Format characters (zero-width, direction overrides, soft hyphen): dropped.
_INVISIBLE = {"Cf"}


def untrusted(text: str | None) -> str:
    """Make bank text safe to show: one line of visible characters.

    Args:
        text: Text from a bank or a stranger, or None.

    Returns:
        The text on one line: format characters dropped, line breaks and control
        characters turned into spaces, runs of spaces collapsed; at most MAX_TEXT
        long and marked with … when cut; empty for None.
    """
    kept = []
    for char in text or "":
        category = unicodedata.category(char)
        if category in _INVISIBLE:
            continue
        kept.append(" " if category in _BREAKS else char)
    line = " ".join("".join(kept).split())
    return line if len(line) <= MAX_TEXT else line[: MAX_TEXT - 1] + "…"
