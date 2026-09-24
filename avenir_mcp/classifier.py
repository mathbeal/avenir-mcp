"""Payee-to-category classifier based on YNAB transaction history."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_THRESHOLD = float(os.getenv("AVENIR_MCP_CONFIDENCE_THRESHOLD", "0.90"))

# Payment-method prefixes that French bank exports put before the merchant.
_PAYMENT_PREFIX = re.compile(r"^(?:CB|CARTE|PRLV(?: SEPA)?|VIR(?:EMENT)?(?: INST| SEPA)?)\s+")
# A bank account number and everything after it ("- IBAN: FR76…"): private, and
# noise for recognising the merchant.
_IBAN_SUFFIX = re.compile(r"\s*-?\s*IBAN\s*:.*$")
# Everything from an invoice date ("FACT 110126") to the end of the label.
_INVOICE_SUFFIX = re.compile(r"\s+FACT\s+\d{6}\b.*$")
# A masked card number ("525130******2"), a date ("12/01", "12/01/26") or a long reference.
_NOISE = re.compile(r"\b\d{4,}\*+\d*|\b\d{2}/\d{2}(?:/\d{2,4})?\b|\b\d{5,}\b")


def normalize_payee(label: str) -> str:
    """Reduce a bank label to the merchant it names.

    Card payments and transfers of the same merchant carry a different date,
    reference or card number every time. Stripping them lets every payment at
    one shop share a single history.

    Examples:
        >>> normalize_payee("CB ACME OUTDOOR FACT 110126 525130******2")
        'ACME OUTDOOR'
        >>> normalize_payee("Corner Shop")
        'CORNER SHOP'
    """
    text = " ".join(label.upper().split())
    text = _IBAN_SUFFIX.sub("", text)
    text = _PAYMENT_PREFIX.sub("", text)
    text = _INVOICE_SUFFIX.sub("", text)
    text = _NOISE.sub("", text)
    return " ".join(text.split())


def build_payee_history(
    transactions: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Build a frequency table mapping payee names to category counts.

    Only transactions with a non-null category_id are included; uncategorized
    transactions carry no signal and are skipped.

    Args:
        transactions: List of YNAB transaction dicts.

    Returns:
        Dict of the form ``{normalized_payee: {category_id: count}}``, keyed by
        :func:`normalize_payee`.

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
        payee = normalize_payee(tx.get("payee_name") or "")
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
        history: Frequency table from :func:`build_payee_history`, keyed by
            normalized payee.
        categories: Full list of available YNAB categories (id, name).
        threshold: Minimum confidence to set ``auto_classify: True``.

    Returns:
        Dict with keys:

        - ``confidence`` (float 0–1)
        - ``auto_classify`` (bool)
        - ``category_id`` / ``category_name`` if ``auto_classify`` is True
        - ``candidates`` (list of top-3 dicts) if ``auto_classify`` is False;
          empty when the payee has no history
    """
    if threshold is None:
        threshold = _DEFAULT_THRESHOLD

    cat_index = {c["id"]: c["name"] for c in categories}
    payee = normalize_payee(payee_name)

    # Only categories that can still be assigned count: a hidden or deleted one
    # would be suggested as a bare id.
    counts = {cat_id: n for cat_id, n in history.get(payee, {}).items() if cat_id in cat_index}
    if not counts:
        logger.info("No usable history for payee %r — no suggestion", payee)
        return {"confidence": 0.0, "auto_classify": False, "candidates": []}

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
            "category_name": cat_index[top_cat_id],
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
            "category_name": cat_index[cat_id],
            "frequency": count,
        }
        for cat_id, count in sorted_cats[:3]
    ]
    return {"confidence": confidence, "auto_classify": False, "candidates": candidates}
