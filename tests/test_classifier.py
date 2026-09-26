"""Tests for classifier.py — payee history and confidence scoring."""

from __future__ import annotations

import importlib
from typing import Any
from unittest.mock import patch

import pytest

from avenir_mcp import classifier

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_CATEGORIES = [
    {"id": "c1", "name": "Office rent"},
    {"id": "c2", "name": "AWS / Cloud"},
    {"id": "c3", "name": "Marketing"},
]


def _make_tx(payee: str, category_id: str | None) -> dict[str, Any]:
    return {"payee_name": payee, "category_id": category_id}


# ---------------------------------------------------------------------------
# build_payee_history
# ---------------------------------------------------------------------------


def test_build_payee_history_groups_by_payee() -> None:
    """Transactions for the same payee are grouped under its normalized name."""
    txs = [_make_tx("AWS", "c2"), _make_tx("AWS", "c2"), _make_tx("Rent", "c1")]
    result = classifier.build_payee_history(txs)
    assert result == {"AWS": {"c2": 2}, "RENT": {"c1": 1}}


def test_build_payee_history_skips_uncategorized() -> None:
    """Transactions with category_id=None must be silently ignored."""
    txs = [_make_tx("AWS", "c2"), _make_tx("AWS", None)]
    result = classifier.build_payee_history(txs)
    assert result == {"AWS": {"c2": 1}}


def test_build_payee_history_skips_empty_payee() -> None:
    """Transactions with no payee name must be silently ignored."""
    txs: list[dict[str, Any]] = [
        {"payee_name": None, "category_id": "c1"},
        {"payee_name": "", "category_id": "c1"},
    ]
    result = classifier.build_payee_history(txs)
    assert not result


def test_build_payee_history_doctest() -> None:
    """Doctest example: 2 classified AWS + 1 uncategorized → AWS: {c1: 2}."""
    txs: list[dict[str, Any]] = [
        {"payee_name": "AWS", "category_id": "c1"},
        {"payee_name": "AWS", "category_id": "c1"},
        {"payee_name": "AWS", "category_id": None},
    ]
    result = classifier.build_payee_history(txs)
    assert result == {"AWS": {"c1": 2}}


# ---------------------------------------------------------------------------
# score_payee — unknown payee
# ---------------------------------------------------------------------------


def test_unknown_payee_returns_zero_confidence() -> None:
    """An unknown payee gets confidence 0 and is left for review."""
    result = classifier.score_payee("NewVendor", {}, _CATEGORIES)
    assert result.confidence == 0.0
    assert result.auto_classify is False


# ---------------------------------------------------------------------------
# score_payee — high confidence
# ---------------------------------------------------------------------------


def test_known_payee_high_confidence_auto_classify() -> None:
    """5/5 identical classifications → confidence=1.0, auto_classify=True."""
    history = {"AWS": {"c2": 5}}
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.90)
    assert result.confidence == 1.0
    assert result.auto_classify is True
    assert result.category_id == "c2"
    assert result.category_name == "AWS / Cloud"


def test_threshold_boundary_auto_classify() -> None:
    """confidence == threshold should set auto_classify=True."""
    history = {"AWS": {"c2": 9, "c1": 1}}  # confidence = 0.9
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.90)
    assert result.confidence == 0.9
    assert result.auto_classify is True


# ---------------------------------------------------------------------------
# score_payee — low confidence / ambiguous
# ---------------------------------------------------------------------------


def test_known_payee_low_confidence_returns_candidates() -> None:
    """Ambiguous history should return auto_classify=False and top-3 candidates."""
    history = {"AWS": {"c2": 2, "c1": 1, "c3": 1}}  # confidence = 0.5
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.90)
    assert result.confidence == 0.5
    assert result.auto_classify is False
    assert len(result.candidates) <= 3


def test_candidates_ordered_by_frequency() -> None:
    """Candidates should be sorted from most to least frequent."""
    history = {"AWS": {"c3": 3, "c1": 5, "c2": 2}}
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.99)
    freqs = [c.frequency for c in result.candidates]
    assert freqs == sorted(freqs, reverse=True)


def test_candidates_capped_at_three() -> None:
    """Even with many categories in history, candidates is at most 3."""
    cats = [{"id": f"c{i}", "name": f"Cat{i}"} for i in range(10)]
    history = {"X": {f"c{i}": i + 1 for i in range(10)}}
    result = classifier.score_payee("X", history, cats, threshold=0.99)
    assert len(result.candidates) == 3


def test_score_payee_uses_default_threshold_from_env() -> None:
    """A lower default threshold lets a 0.5 confidence auto-classify."""
    # Patch the module-level default
    with patch.object(classifier, "_DEFAULT_THRESHOLD", 0.50):
        history = {"AWS": {"c2": 1, "c1": 1}}  # confidence = 0.5
        result = classifier.score_payee("AWS", history, _CATEGORIES)
    # With threshold=0.5, confidence=0.5 should auto-classify
    assert result.auto_classify is True


def test_default_threshold_is_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """AVENIR_MCP_CONFIDENCE_THRESHOLD sets the default threshold at import time."""
    monkeypatch.setenv("AVENIR_MCP_CONFIDENCE_THRESHOLD", "0.75")
    try:
        reloaded = importlib.reload(classifier)
        assert reloaded._DEFAULT_THRESHOLD == 0.75  # pylint: disable=protected-access
    finally:
        monkeypatch.delenv("AVENIR_MCP_CONFIDENCE_THRESHOLD")
        importlib.reload(classifier)


# ---------------------------------------------------------------------------
# normalize_payee — bank labels reduced to the merchant
# ---------------------------------------------------------------------------


# Built at run time so that no IBAN-shaped string sits in the repository.
_FAKE_IBAN = "FR" + "00" + "1" * 23


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("CB ACME OUTDOOR FACT 110126 525130******2", "ACME OUTDOOR"),
        ("CB WWW.EXAMPLE.IO FACT 220126 525130******2", "WWW.EXAMPLE.IO"),
        ("CB FOO BAR 525130******2", "FOO BAR"),
        ("VIR INST GARAGE MARTIN", "GARAGE MARTIN"),
        ("VIR SEPA JOHN SMITH", "JOHN SMITH"),
        ("PRLV SEPA MOBILE TELECOM", "MOBILE TELECOM"),
        ("CARTE 12/01 BAKERY ROSE", "BAKERY ROSE"),
        ("Corner Shop", "CORNER SHOP"),
        ("  corner   shop ", "CORNER SHOP"),
        ("ONLINE STORE 1234567890", "ONLINE STORE"),
        ("INSURER - PRELEV - IBAN: " + _FAKE_IBAN, "INSURER - PRELEV"),
        ("TAX OFFICE - REF 123 - IBAN: " + _FAKE_IBAN, "TAX OFFICE - REF 123"),
        ("", ""),
    ],
)
def test_normalize_payee(label: str, expected: str) -> None:
    """Card prefixes, invoice dates, masked card numbers and references are removed."""
    assert classifier.normalize_payee(label) == expected


def test_build_payee_history_groups_labels_of_the_same_merchant() -> None:
    """Two card payments at the same shop on different days share one history."""
    txs = [
        {"payee_name": "CB ACME OUTDOOR FACT 110126 525130******2", "category_id": "c1"},
        {"payee_name": "CB ACME OUTDOOR FACT 140226 525130******2", "category_id": "c1"},
    ]
    assert classifier.build_payee_history(txs) == {"ACME OUTDOOR": {"c1": 2}}


def test_score_payee_recognises_a_new_label_of_a_known_merchant() -> None:
    """A payment dated differently from past ones still matches its merchant."""
    history = classifier.build_payee_history(
        [{"payee_name": "CB ACME OUTDOOR FACT 110126 525130******2", "category_id": "c1"}]
    )
    result = classifier.score_payee(
        "CB ACME OUTDOOR FACT 300926 525130******2", history, _CATEGORIES
    )
    assert result.auto_classify is True
    assert result.category_id == "c1"


def test_score_payee_unknown_payee_returns_no_candidates() -> None:
    """With no history there is nothing to suggest: no dump of every category."""
    result = classifier.score_payee("NEVER SEEN", {}, _CATEGORIES)
    assert result == classifier.Score(confidence=0.0, auto_classify=False)


def test_score_payee_ignores_categories_no_longer_available() -> None:
    """History pointing to a hidden or deleted category suggests nothing, not a raw id."""
    history = {"ATM": {"c-hidden": 5}}
    result = classifier.score_payee("ATM", history, _CATEGORIES)
    assert result == classifier.Score(confidence=0.0, auto_classify=False)


def test_score_payee_counts_only_available_categories() -> None:
    """Past assignments to a vanished category do not dilute the confidence."""
    history = {"AWS": {"c-hidden": 9, "c2": 3}}
    result = classifier.score_payee("AWS", history, _CATEGORIES)
    assert result.auto_classify is True
    assert result.category_id == "c2"
