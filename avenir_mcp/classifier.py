"""Payee-to-category classifier based on YNAB transaction history."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLD = float(os.getenv("AVENIR_MCP_CONFIDENCE_THRESHOLD", "0.90"))


def build_payee_history(
    transactions: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Build a frequency table mapping payee names to category counts.

    Only transactions with a non-null category_id are included; uncategorized
    transactions carry no signal and are skipped.

    Args:
        transactions: List of YNAB transaction dicts.

    Returns:
        Dict of the form ``{payee_name: {category_id: count}}``.

    Examples:
        >>> txs = [
        ...     {"payee_name": "AWS", "category_id": "c1"},
        ...     {"payee_name": "AWS", "category_id": "c1"},
        ...     {"payee_name": "AWS", "category_id": None},
        ... ]
        >>> build_payee_history(txs)
        {'AWS': {'c1': 2}}
    """
    history: dict[str, dict[str, int]] = {}
    for tx in transactions:
        payee = tx.get("payee_name") or ""
        category_id = tx.get("category_id")
        if not payee or not category_id:
            continue
        if payee not in history:
            history[payee] = {}
        history[payee][category_id] = history[payee].get(category_id, 0) + 1
    return history


def score_payee(
    payee_name: str,
    history: dict[str, dict[str, int]],
    categories: list[dict[str, Any]],
    threshold: float | None = None,
) -> dict[str, Any]:
    """Compute a confidence score and suggest categories for a payee.

    The confidence score is the fraction of historical transactions for this
    payee that were assigned to the top category:
    ``confidence = top_count / total_count``.

    Args:
        payee_name: Name of the payee to classify.
        history: Frequency table from :func:`build_payee_history`.
        categories: Full list of available YNAB categories (id, name).
        threshold: Minimum confidence to set ``auto_classify: True``.

    Returns:
        Dict with keys:

        - ``confidence`` (float 0–1)
        - ``auto_classify`` (bool)
        - ``category_id`` / ``category_name`` if ``auto_classify`` is True
        - ``candidates`` (list of top-3 dicts) if ``auto_classify`` is False
    """
    if threshold is None:
        threshold = _DEFAULT_THRESHOLD

    cat_index = {c["id"]: c["name"] for c in categories}

    if payee_name not in history:
        logger.info("Unknown payee %r — returning all categories as candidates", payee_name)
        candidates = [{"category_id": c["id"], "category_name": c["name"]} for c in categories]
        return {"confidence": 0.0, "auto_classify": False, "candidates": candidates}

    counts = history[payee_name]
    total = sum(counts.values())
    sorted_cats = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    top_cat_id, top_count = sorted_cats[0]
    confidence = top_count / total

    if confidence >= threshold:
        logger.info(
            "Payee %r → category %r (confidence=%.2f ≥ %.2f)",
            payee_name,
            top_cat_id,
            confidence,
            threshold,
        )
        return {
            "confidence": confidence,
            "auto_classify": True,
            "category_id": top_cat_id,
            "category_name": cat_index.get(top_cat_id, top_cat_id),
        }

    logger.info(
        "Payee %r → ambiguous (confidence=%.2f < %.2f) — returning top-3 candidates",
        payee_name,
        confidence,
        threshold,
    )
    candidates = [
        {
            "category_id": cat_id,
            "category_name": cat_index.get(cat_id, cat_id),
            "frequency": count,
        }
        for cat_id, count in sorted_cats[:3]
    ]
    return {"confidence": confidence, "auto_classify": False, "candidates": candidates}
