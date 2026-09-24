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
    """Transactions for the same payee should be grouped together."""
    txs = [_make_tx("AWS", "c2"), _make_tx("AWS", "c2"), _make_tx("Rent", "c1")]
    result = classifier.build_payee_history(txs)
    assert result == {"AWS": {"c2": 2}, "Rent": {"c1": 1}}


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


def test_unknown_payee_returns_all_categories() -> None:
    """An unknown payee should return confidence=0 and all categories."""
    result = classifier.score_payee("NewVendor", {}, _CATEGORIES)
    assert result["confidence"] == 0.0
    assert result["auto_classify"] is False
    assert len(result["candidates"]) == len(_CATEGORIES)


# ---------------------------------------------------------------------------
# score_payee — high confidence
# ---------------------------------------------------------------------------


def test_known_payee_high_confidence_auto_classify() -> None:
    """5/5 identical classifications → confidence=1.0, auto_classify=True."""
    history = {"AWS": {"c2": 5}}
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.90)
    assert result["confidence"] == 1.0
    assert result["auto_classify"] is True
    assert result["category_id"] == "c2"
    assert result["category_name"] == "AWS / Cloud"


def test_threshold_boundary_auto_classify() -> None:
    """confidence == threshold should set auto_classify=True."""
    history = {"AWS": {"c2": 9, "c1": 1}}  # confidence = 0.9
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.90)
    assert result["confidence"] == 0.9
    assert result["auto_classify"] is True


# ---------------------------------------------------------------------------
# score_payee — low confidence / ambiguous
# ---------------------------------------------------------------------------


def test_known_payee_low_confidence_returns_candidates() -> None:
    """Ambiguous history should return auto_classify=False and top-3 candidates."""
    history = {"AWS": {"c2": 2, "c1": 1, "c3": 1}}  # confidence = 0.5
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.90)
    assert result["confidence"] == 0.5
    assert result["auto_classify"] is False
    assert "candidates" in result
    assert len(result["candidates"]) <= 3


def test_candidates_ordered_by_frequency() -> None:
    """Candidates should be sorted from most to least frequent."""
    history = {"AWS": {"c3": 3, "c1": 5, "c2": 2}}
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.99)
    freqs = [c["frequency"] for c in result["candidates"]]
    assert freqs == sorted(freqs, reverse=True)


def test_candidates_capped_at_three() -> None:
    """Even with many categories in history, candidates is at most 3."""
    cats = [{"id": f"c{i}", "name": f"Cat{i}"} for i in range(10)]
    history = {"X": {f"c{i}": i + 1 for i in range(10)}}
    result = classifier.score_payee("X", history, cats, threshold=0.99)
    assert len(result["candidates"]) == 3


def test_category_name_falls_back_to_id_if_unknown() -> None:
    """If a category_id from history is not in the categories list, use the id as name."""
    history = {"AWS": {"c_unknown": 5}}
    result = classifier.score_payee("AWS", history, _CATEGORIES, threshold=0.90)
    assert result["category_name"] == "c_unknown"


def test_score_payee_uses_default_threshold_from_env() -> None:
    """A lower default threshold lets a 0.5 confidence auto-classify."""
    # Patch the module-level default
    with patch.object(classifier, "_DEFAULT_THRESHOLD", 0.50):
        history = {"AWS": {"c2": 1, "c1": 1}}  # confidence = 0.5
        result = classifier.score_payee("AWS", history, _CATEGORIES)
    # With threshold=0.5, confidence=0.5 should auto-classify
    assert result["auto_classify"] is True


def test_default_threshold_is_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """AVENIR_MCP_CONFIDENCE_THRESHOLD sets the default threshold at import time."""
    monkeypatch.setenv("AVENIR_MCP_CONFIDENCE_THRESHOLD", "0.75")
    try:
        reloaded = importlib.reload(classifier)
        assert reloaded._DEFAULT_THRESHOLD == 0.75  # pylint: disable=protected-access
    finally:
        monkeypatch.delenv("AVENIR_MCP_CONFIDENCE_THRESHOLD")
        importlib.reload(classifier)
