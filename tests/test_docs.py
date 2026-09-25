"""The documentation cannot drift from the code."""

from __future__ import annotations

import re
from pathlib import Path

from docsgen import examples, reference

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REGENERATE = "run `uv run python -m docsgen` and commit the result"


def test_tool_reference_matches_the_server() -> None:
    """docs/reference/tools.md is what the server declares today."""
    committed = (DOCS / "reference" / "tools.md").read_text(encoding="utf-8")
    assert committed == reference.generate(), REGENERATE


def test_examples_are_what_avenir_returns_on_the_demo_budget() -> None:
    """Every JSON example in the docs is a real, current answer."""
    for name, text in examples.generate().items():
        committed = (DOCS / "snippets" / f"{name}.json").read_text(encoding="utf-8")
        assert committed == text, f"{name}: {REGENERATE}"


def test_every_environment_variable_is_documented() -> None:
    """A variable the code reads is explained on the configuration page."""
    source = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "avenir_mcp").glob("*.py"))
    used = set(re.findall(r'os\.getenv\("([A-Z_]+)"', source))
    page = (DOCS / "reference" / "configuration.md").read_text(encoding="utf-8")
    assert used, "the code should read at least YNAB_API_KEY"
    assert not {name for name in used if f"`{name}`" not in page}


def test_every_snippet_is_used_by_a_page() -> None:
    """No example is generated for nothing."""
    pages = "\n".join(p.read_text(encoding="utf-8") for p in DOCS.rglob("*.md"))
    unused = [p.name for p in (DOCS / "snippets").glob("*.json") if p.name not in pages]
    assert not unused
