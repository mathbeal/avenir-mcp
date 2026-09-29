"""Reading YNAB's API terms from its page, and noticing when YNAB changes them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from docsgen import terms

_PAGE = """<h2>Intro</h2><p>Not the terms.</p>
<h2>Legal</h2><section><h3 id="terms">API Terms of Service</h3>
<p>Last updated: May 28, 2025</p>
<p>We are not affiliated with YNAB. The official YNAB website can be found at
<a href="https://www.ynab.com">https://www.ynab.com</a>. The names YNAB and You Need A
Budget are registered trademarks of YNAB.</p></section>
<section><div class="papi-version"><h3 id="v1.87.0">v1.87.0</h3></div></section>"""


def test_the_terms_are_read_between_the_legal_heading_and_the_changelog() -> None:
    """Date as YYYY-MM-DD, the attribution as a reader sees it, a fingerprint of the rest."""
    found = terms.terms(_PAGE)
    assert found["last_updated"] == "2025-05-28"
    assert found["attribution"] == (
        "We are not affiliated with YNAB. The official YNAB website can be found at "
        "https://www.ynab.com. The names YNAB and You Need A Budget are registered "
        "trademarks of YNAB."
    )
    assert len(found["sha256"]) == 64
    assert terms.terms(_PAGE.replace("Not the terms.", "Other intro."))["sha256"] == found["sha256"]
    assert terms.terms(_PAGE.replace("Budget are", "Budget, are"))["sha256"] != found["sha256"]


@pytest.mark.parametrize(
    ("page", "expected"),
    [
        (_PAGE.replace("<h2>Legal</h2>", "<h2>Other</h2>"), "no longer where they were"),
        (_PAGE.replace("Last updated", "Updated"), "no longer where they were"),
        (_PAGE.replace("We are not affiliated", "We are"), "attribution"),
    ],
)
def test_a_page_that_moved_the_terms_says_to_read_them(page: str, expected: str) -> None:
    """If the terms are not where they were, the check stops rather than guess."""
    with pytest.raises(ValueError, match=expected):
        terms.terms(page)


def test_the_check_passes_fails_and_updates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unchanged: 0. Changed: 1 and what to do. --update: the snapshot is rewritten."""
    known: dict[str, Any] = terms.terms(_PAGE)
    snapshot = tmp_path / "ynab-terms.json"
    snapshot.write_text(json.dumps(known), encoding="utf-8")
    monkeypatch.setattr(terms, "SNAPSHOT", snapshot)
    monkeypatch.setattr(terms, "_live", lambda: known)
    assert terms.main([]) == 0
    changed = terms.terms(_PAGE.replace("May 28, 2025", "June 3, 2026"))
    monkeypatch.setattr(terms, "_live", lambda: changed)
    assert terms.main([]) == 1
    assert "--update" in capsys.readouterr().out
    assert terms.main(["--update"]) == 0
    assert json.loads(snapshot.read_text(encoding="utf-8"))["last_updated"] == "2026-06-03"


def test_the_snapshot_holds_the_terms_avenir_mcp_was_checked_against() -> None:
    """A date, a fingerprint and the attribution, as read on api.ynab.com."""
    known = terms.snapshot()
    assert known["last_updated"] == "2025-05-28"
    assert len(known["sha256"]) == 64
    assert known["attribution"].startswith("We are not affiliated")
