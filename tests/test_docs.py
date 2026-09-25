"""The documentation cannot drift from the code, nor one language from another."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from docsgen import pages

CONTENT = pages.CONTENT
TRANSLATED = ("fr", "es")
REGENERATE = "run `uv run python -m docsgen` and commit the result"


def _english_pages() -> set[Path]:
    return {
        p.relative_to(CONTENT)
        for p in CONTENT.rglob("*.md*")
        if p.relative_to(CONTENT).parts[0] not in TRANSLATED
    }


def test_generated_files_are_current() -> None:
    """Tool reference, security page and every JSON example match the code today."""
    for path, text in pages.generated().items():
        assert path.read_text(encoding="utf-8") == text, f"{path.name}: {REGENERATE}"


@pytest.mark.parametrize("language", TRANSLATED)
def test_every_written_page_is_translated(language: str) -> None:
    """French and Spanish have every hand-written page English has, and no other."""
    generated = {p.relative_to(CONTENT) for p in pages.generated() if p.suffix == ".md"}
    english = _english_pages() - generated
    translated = {p.relative_to(CONTENT / language) for p in (CONTENT / language).rglob("*.md*")}
    assert translated == english


@pytest.mark.parametrize("language", ("", *TRANSLATED))
def test_every_environment_variable_is_documented(language: str) -> None:
    """A variable the code reads is explained on the configuration page, in each language."""
    source = "\n".join(
        p.read_text(encoding="utf-8") for p in (pages.ROOT / "avenir_mcp").glob("*.py")
    )
    used = set(re.findall(r'os\.getenv\("([A-Z_]+)"', source))
    page = (CONTENT / language / "reference" / "configuration.mdx").read_text(encoding="utf-8")
    assert used, "the code should read at least YNAB_API_KEY"
    assert not {name for name in used if f"`{name}`" not in page}


def test_every_snippet_is_used_by_a_page() -> None:
    """No example is generated for nothing."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in CONTENT.rglob("*.md*"))
    unused = [p.name for p in pages.SNIPPETS.glob("*.json") if f"@snippets/{p.name}" not in text]
    assert not unused
