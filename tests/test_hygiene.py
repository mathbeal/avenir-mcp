# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The repository must never carry real financial data or secrets."""

from __future__ import annotations

import re
import subprocess  # noqa: S404  # nosec B404 - runs git ls-files
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIPPED_DIRS = {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pdf", ".csv", ".ofx", ".qif"}
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,3})?\b")
YNAB_TOKEN = re.compile(r"YNAB_API_KEY\s*=\s*['\"]?[A-Za-z0-9_-]{20,}")


# A home directory in an absolute path says who and where: /Users/name, /home/name.
HOME_PATH = re.compile(rb"/(?:Users|home)/[A-Za-z0-9._-]+/")
# iCloud Drive and Finder copies: "notes 2.md", ".coverage 3".
DUPLICATE = re.compile(r".+ \d+(\.[^.]+)?$")


def _repository_files() -> list[Path]:
    """Files git tracks, or every file when there is no repository (an sdist)."""
    if (ROOT / ".git").exists():
        listed = subprocess.run(  # noqa: S603  # nosec B603 - fixed argument list
            ["git", "ls-files", "-z"],  # noqa: S607 - git from PATH, as the developer runs it
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        return [ROOT / name for name in listed.decode().split("\0") if name]
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
        if path.name == "test_hygiene.py" or not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if IBAN.search(text) or YNAB_TOKEN.search(text):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders


def test_home_detector_recognises_a_home_path() -> None:
    """Positive control for the home-path pattern."""
    assert HOME_PATH.search(b"/Users/someone/project/file.py")
    assert HOME_PATH.search(b"/home/someone/.cache")
    assert DUPLICATE.match(".coverage 2")
    assert DUPLICATE.match("notes 3.md")


def test_no_home_path_or_icloud_copy_in_repository() -> None:
    """No tracked file names a home directory, text or binary; no Finder copy is tracked."""
    offenders = []
    for path in _repository_files():
        if path.name == "test_hygiene.py" or not path.exists():
            continue
        if DUPLICATE.match(path.name) or HOME_PATH.search(path.read_bytes()):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders
