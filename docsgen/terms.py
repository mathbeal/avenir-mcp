"""YNAB's API terms, as avenir-mcp checks itself against them, and YNAB's changes caught.

YNAB publishes its API Terms of Service on api.ynab.com with a "Last updated" date and
no version. `api/ynab-terms.json` keeps that date, a fingerprint of the terms' text and
the attribution every app must display, word for word. `python -m docsgen.terms`
compares them with the page as published today and fails when YNAB changed its terms:
read the new terms, adapt the checks marked `ynab_terms`, then `--update`.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from docsgen import snapshots

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "api" / "ynab-terms.json"
TERMS_URL = "https://api.ynab.com/"
_ATTRIBUTION = re.compile(r"We are not affiliated.*?registered trademarks of YNAB\.", re.S)
_UPDATED = re.compile(r"Last updated:\s*([A-Z][a-z]+ \d{1,2}, \d{4})")


def text_of(fragment: str) -> str:
    """Reduce HTML to its words, one space between them.

    Args:
        fragment: Part of a page.

    Returns:
        The text, tags removed, entities decoded, whitespace collapsed, no space
        before punctuation (a closing link tag left one).
    """
    words = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())
    return re.sub(r" ([.,;:!?])", r"\1", words)


def terms(page: str) -> dict[str, Any]:
    """Find the terms in the page YNAB publishes.

    Args:
        page: The HTML of api.ynab.com.

    Returns:
        Their "Last updated" date (YYYY-MM-DD), the SHA-256 of their text and the
        attribution every app must display.

    Raises:
        ValueError: If the page no longer has the terms where they were.
    """
    start = page.find("<h2>Legal</h2>")
    end = page.find('class="papi-version"', start)
    updated = _UPDATED.search(page[start:end] if start >= 0 else "")
    if start < 0 or end < 0 or updated is None:
        raise ValueError(f"The terms are no longer where they were on {TERMS_URL}: read them.")
    body = text_of(page[start:end])
    attribution = _ATTRIBUTION.search(body)
    if attribution is None:
        raise ValueError("The attribution text is no longer in the terms: read them.")
    return {
        "last_updated": datetime.strptime(updated.group(1), "%B %d, %Y").date().isoformat(),
        "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "attribution": attribution.group(0),
    }


def snapshot() -> dict[str, Any]:
    """Read the terms avenir-mcp was last checked against.

    Returns:
        Their date, fingerprint and attribution.
    """
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _live() -> dict[str, Any]:
    """Read the terms as YNAB publishes them today.

    Returns:
        Their date, fingerprint and attribution.
    """
    response = httpx.get(TERMS_URL, timeout=30, follow_redirects=True)
    response.raise_for_status()
    return terms(response.text)


def main(argv: list[str] | None = None) -> int:
    """Compare the snapshot with YNAB's terms as published today, or update it.

    Args:
        argv: The command-line arguments; None for sys.argv.

    Returns:
        0 when nothing changed (or the snapshot was updated), 1 otherwise.
    """
    update = snapshots.update_requested(argv, __doc__)
    live = _live()
    if update:
        SNAPSHOT.write_text(json.dumps(live, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Snapshot updated: YNAB API terms of {live['last_updated']}.")
        return 0
    known = snapshot()
    if live == known:
        print(f"YNAB API terms of {known['last_updated']}: unchanged.")
        return 0
    print(
        f"YNAB changed its API terms ({known['last_updated']} -> {live['last_updated']}). "
        "Read them on https://api.ynab.com/#terms, adapt the checks marked ynab_terms, then "
        "run `uv run python -m docsgen.terms --update`."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
