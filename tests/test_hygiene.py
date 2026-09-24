"""The repository must never carry real financial data or secrets."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIPPED_DIRS = {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pdf", ".csv", ".ofx", ".qif"}
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,3})?\b")
YNAB_TOKEN = re.compile(r"YNAB_API_KEY\s*=\s*['\"]?[A-Za-z0-9_-]{20,}")


def _repository_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not SKIPPED_DIRS.intersection(path.relative_to(ROOT).parts)
        and path.name != ".env"
    ]


def test_detectors_recognise_known_samples() -> None:
    """Positive control: a pattern that never matches would prove nothing."""
    assert IBAN.search("FR76 3000 6000 0112 3456 7890 189")
    assert YNAB_TOKEN.search("YNAB_API_KEY=abcdefghijklmnopqrstuvwxyz012345")


def test_no_financial_documents_in_repository() -> None:
    """Statements and exports stay out of the repository."""
    found = [p.name for p in _repository_files() if p.suffix.lower() in FORBIDDEN_SUFFIXES]
    assert not found


def test_no_iban_or_token_in_repository() -> None:
    """No text file contains an IBAN or a YNAB token."""
    offenders = []
    for path in _repository_files():
        if path.name == "test_hygiene.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if IBAN.search(text) or YNAB_TOKEN.search(text):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders
