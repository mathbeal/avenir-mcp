# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for text.py — bank text made safe to show to a person or an agent."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from avenir_mcp import text

_ynab_text: TypeAdapter[str] = TypeAdapter(text.YnabText)


def test_line_breaks_become_spaces() -> None:
    """A payee cannot add lines of its own to a confirmation question."""
    forged = "SHOP\n- 2026-09-02 RENT 0.00: Rent → Rent\r\n\u2028(nothing else)\tend"
    assert text.untrusted(forged) == "SHOP - 2026-09-02 RENT 0.00: Rent → Rent (nothing else) end"


def test_invisible_and_direction_characters_are_removed() -> None:
    """Zero-width and right-to-left overrides cannot disguise what is shown."""
    assert text.untrusted("PAY\u202eLAPYAP\u200b\u2066X\ufeff\u00ad") == "PAYLAPYAPX"


def test_long_text_is_cut_and_marked() -> None:
    """One label cannot flood the context or the question."""
    cut = text.untrusted("X" * 300)
    assert len(cut) == text.MAX_TEXT
    assert cut.endswith("…")


def test_missing_text_is_empty() -> None:
    """No payee reads as an empty string."""
    assert text.untrusted(None) == ""
    assert text.untrusted("   ") == ""


def test_ordinary_text_is_kept() -> None:
    """Accents, symbols and single spaces are left as they are."""
    assert text.untrusted("Boulangerie du Port — 12,50 €") == "Boulangerie du Port — 12,50 €"


def test_text_of_exactly_the_maximum_length_is_not_cut() -> None:
    """Eighty characters fit: no ellipsis."""
    exact = "x" * text.MAX_TEXT
    assert text.untrusted(exact) == exact


def test_text_without_a_nul_is_sent_as_it_is() -> None:
    """YnabText only refuses NUL: everything else, accents included, goes through."""
    assert _ynab_text.validate_python("Boulangerie du Port — 12,50 €") == (
        "Boulangerie du Port — 12,50 €"
    )


def test_a_nul_is_refused_and_the_message_names_it() -> None:
    """The agent is told which character YNAB rejects and what to do, not just that it failed."""
    with pytest.raises(ValidationError) as refusal:
        _ynab_text.validate_python("Shop\x00")
    assert refusal.value.errors()[0]["msg"] == (
        "Value error, contains a NUL character (U+0000), which YNAB refuses: remove it"
    )


def test_a_name_on_one_line_is_kept() -> None:
    """one_line refuses nothing an ordinary category or payee name holds."""
    assert text.one_line("Côté Jardin — n°2") == "Côté Jardin — n°2"


@pytest.mark.parametrize(
    "name",
    [
        "Rent\u200bArrears",
        "Rent\nArrears",
        "Rent\u202eArrears",
        "Rent\u2028Arrears",
        "Rent\tArrears",
    ],
    ids=["zero-width", "line break", "direction override", "line separator", "tab"],
)
def test_a_name_that_would_not_show_on_one_line_is_refused(name: str) -> None:
    """A break, control or format character in a name the agent chose is refused."""
    with pytest.raises(ValueError, match="one line"):
        text.one_line(name)


def test_the_refused_name_is_quoted_back_safely_with_what_to_do() -> None:
    """The message shows the name made safe, so it cannot forge a line of the question."""
    with pytest.raises(ValueError) as refusal:
        text.one_line("Rent\u200bArrears")
    assert str(refusal.value) == (
        "'RentArrears' contains a line break, control or format character (such as a "
        "zero-width or direction mark): give the name on one line, with visible "
        "characters only."
    )
