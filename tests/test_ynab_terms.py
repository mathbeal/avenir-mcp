# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""What the "YNAB API terms: self-checked" badge promises, checked on every change.

Each test marked `ynab_terms` enforces one rule of YNAB's API Terms of Service, as
dated in api/ynab-terms.json; `python -m docsgen.terms` fails when YNAB changes them.
Self-checked means exactly that: the checks are the project's own. YNAB lists avenir-mcp
among the third-party apps of its "Works with YNAB" directory, and endorses nothing.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp import Client

from avenir_mcp import client, server
from docsgen import terms

pytestmark = pytest.mark.ynab_terms

ROOT = Path(__file__).resolve().parent.parent
TERMS = json.loads((ROOT / "api" / "ynab-terms.json").read_text(encoding="utf-8"))
OFFICIAL_IMAGE = "https://api.ynab.com/papi/works_with_ynab.svg"
DIRECTORY = "https://api.ynab.com/#works-with-ynab-third-party"
LISTED_IMAGE = f"[![Works with YNAB]({OFFICIAL_IMAGE})]({DIRECTORY})"
# What the project may say about the listing: a fact and its limit, nothing in between.
LISTING = (
    "Listed by YNAB in its Works with YNAB directory, among third-party apps. Not endorsed by YNAB."
)
LANGUAGES = ["", "fr", "es", "de", "nl"]


def _words(markdown: str) -> str:
    """The text a reader sees: quote marks, emphasis and link syntax removed."""
    plain = re.sub(r"^>\s?", "", markdown, flags=re.M)
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", plain).replace("**", "")
    return terms.text_of(plain)


def test_the_readme_displays_ynabs_attribution_word_for_word() -> None:
    """YNAB asks every app to display its non-affiliation text as written."""
    readme = _words((ROOT / "README.md").read_text(encoding="utf-8"))
    assert TERMS["attribution"] in readme


def test_the_site_footer_displays_ynabs_attribution_word_for_word() -> None:
    """The English footer of every documentation page carries the same text."""
    footer = (ROOT / "docs" / "src" / "components" / "home-i18n.ts").read_text(encoding="utf-8")
    english = footer[footer.index("en:") : footer.index("fr:")]
    assert TERMS["attribution"] in terms.text_of(english.replace("\\'", "'"))


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_legal_page_quotes_ynabs_attribution_word_for_word(language: str) -> None:
    """The legal notice, in each language, quotes YNAB's text as written before translating it."""
    page = ROOT / "docs" / "src" / "content" / "docs" / language / "project" / "legal.mdx"
    assert TERMS["attribution"] in _words(page.read_text(encoding="utf-8").replace("*", ""))


def test_only_ynabs_own_image_stands_for_ynab() -> None:
    """The "Works with YNAB" image is YNAB's, linked unmodified; no copy lives here."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^)]*ynab[^)]*)\)", readme, flags=re.I)
    # A workflow's status badge is GitHub's image, not YNAB artwork.
    artwork = [url for url in images if not url.startswith("https://github.com/")]
    assert artwork == [OFFICIAL_IMAGE]
    copies = [p for p in ROOT.rglob("*ynab*") if p.suffix in {".svg", ".png", ".jpg", ".webp"}]
    assert [p for p in copies if ".venv" not in p.parts and "node_modules" not in p.parts] == []


def test_no_tool_asks_for_anyones_ynab_token() -> None:
    """A personal token serves its owner only: no tool takes a token from whoever calls it."""
    server.configure(enable_writes=True)

    async def schemas() -> list[dict[str, Any]]:
        async with Client(server.mcp) as mcp_client:
            return [t.input_schema for t in await mcp_client.list_tools()]

    names = {name for schema in asyncio.run(schemas()) for name in schema.get("properties", {})}
    assert not {n for n in names if re.search(r"token|api_?key|password|secret", n, re.I)}


def test_the_http_transport_listens_on_this_machine_unless_told_otherwise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Serving others would need YNAB's OAuth: by default nothing outside the machine connects."""
    monkeypatch.setenv("AVENIR_MCP_TRANSPORT", "http")
    monkeypatch.delenv("AVENIR_MCP_HOST", raising=False)
    with patch.object(server.mcp, "run") as run:
        server.main([])
    assert run.call_args.kwargs["host"] == "127.0.0.1"


def test_requests_stay_under_ynabs_hourly_limit() -> None:
    """YNAB allows 200 requests an hour per token; the pacer keeps a margin below it."""
    assert client.PACE.budget < 200


def test_the_readme_dates_the_badge_with_the_terms_checked() -> None:
    """The badge's promise names the terms it holds against, and the workflow that checks."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "actions/workflows/ynab-terms.yml/badge.svg" in readme
    assert f"YNAB's API terms of {TERMS['last_updated']}" in readme


def test_the_readme_says_avenir_mcp_is_listed_by_ynab_and_claims_nothing_more() -> None:
    """The README states the listing as a fact, links it, and says YNAB endorses nothing."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert LISTED_IMAGE in readme
    assert LISTING in _words(readme)


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_home_page_links_ynabs_image_to_the_entry_that_lists_avenir_mcp(
    language: str,
) -> None:
    """Each home page shows YNAB's own image, linked to the third-party part of its directory."""
    page = ROOT / "docs" / "src" / "content" / "docs" / language / "index.mdx"
    assert LISTED_IMAGE in page.read_text(encoding="utf-8")
