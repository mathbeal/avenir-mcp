# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The one-click install links say what `docsgen.install` says, decoded.

A link carries the server's configuration encoded, which no reader and no review can
check by eye. These tests decode every link the generator produces, and every link
written in the documentation, and compare what comes out with the one configuration
`docsgen.install` defines.
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

from docsgen import install, pages

LANGUAGES = tuple(install.PLACEHOLDERS)


def _query(link: str, parameter: str) -> str:
    """One parameter of a link's query, URL-encoding undone."""
    (value,) = parse_qs(urlsplit(link).query, keep_blank_values=True)[parameter]
    return value


def _decoded(link: str) -> dict[str, Any]:
    """What an editor reads from a link: its JSON payload, decoded the way it does."""
    if link.startswith("vscode:"):
        return dict(json.loads(unquote(urlsplit(link).query)))
    return dict(json.loads(base64.b64decode(_query(link, "config"))))


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_cursor_link_installs_avenir_mcp_with_the_token_to_replace(language: str) -> None:
    """Cursor's link holds the entry of the page's own language, nothing more."""
    link = install.cursor(language)
    assert link.startswith("cursor://anysphere.cursor-deeplink/mcp/install?")
    assert _query(link, "name") == "avenir-mcp"
    assert _decoded(link) == install.server(install.PLACEHOLDERS[language])


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_lm_studio_link_installs_avenir_mcp_with_the_token_to_replace(language: str) -> None:
    """LM Studio's link holds the same entry, its base64 URL-encoded as LM Studio writes it."""
    link = install.lm_studio(language)
    assert link.startswith("lmstudio://add_mcp?")
    assert _query(link, "name") == "avenir-mcp"
    assert "%3D" in link or "=" not in _query(link, "config")
    assert _decoded(link) == install.server(install.PLACEHOLDERS[language])


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_vs_code_link_asks_for_the_token_in_a_password_box(language: str) -> None:
    """VS Code's link names the server, runs uvx avenir-mcp, and hides the token typed."""
    payload = _decoded(install.vs_code(language))
    (token,) = payload.pop("inputs")
    assert payload.pop("name") == "avenir-mcp"
    assert payload.pop("type") == "stdio"
    assert payload == install.server(f"${{input:{token['id']}}}")
    assert token == {
        "type": "promptString",
        "id": install.INPUT_ID,
        "description": install.PROMPTS[language],
        "password": True,
    }


def test_no_link_enables_writes_or_carries_a_real_token() -> None:
    """One click installs avenir-mcp read-only, with a placeholder instead of a token."""
    every = [link for language in LANGUAGES for link in install.links(language).values()]
    assert len(every) == 3 * len(LANGUAGES)
    for link in every:
        assert "AVENIR_MCP_WRITE" not in json.dumps(_decoded(link)) + link
    assert {install.PLACEHOLDERS[language] for language in LANGUAGES} == {
        "your-token",
        "votre-jeton",
        "su-token",
        "ihr-token",
        "uw-token",
    }


_DEEPLINK = re.compile(r"(?:cursor://|lmstudio://|vscode:mcp/install\?)[^\s)\"'<]+")


def _written(language: str) -> list[str]:
    """Every one-click link the documentation of a language carries.

    The install page imports them from the generated snippet; the page itself and the
    README are read too, so a link pasted there by hand is caught as well.
    """
    sources = [
        pages.SNIPPETS / language / "install_links.json",
        pages.CONTENT / language / "getting-started" / "install.mdx",
    ]
    if not language:
        sources.append(pages.ROOT / "README.md")
    return [link for source in sources for link in _DEEPLINK.findall(source.read_text("utf-8"))]


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_link_of_the_documentation_carries_the_reference_configuration(
    language: str,
) -> None:
    """A link written in a page decodes to the configuration of `docsgen.install`.

    `python -m docsgen.install` prints the links. A page edited by hand, a placeholder
    changed in one language only, or an editor that changes its format is caught here
    instead of sending a reader an install that cannot work.
    """
    generated = set(install.links(language).values())
    written = _written(language)
    assert generated <= set(written), f"{language or 'en'}: a link of the page is missing"
    for link in written:
        assert link in generated, f"{language or 'en'}: run `uv run python -m docsgen.install`"
        payload = _decoded(link)
        if link.startswith("vscode:"):
            (token,) = payload["inputs"]
            assert token["password"] is True
            assert payload["env"] == {"YNAB_API_KEY": f"${{input:{token['id']}}}"}
            assert (payload["command"], payload["args"]) == (install.COMMAND, [install.NAME])
        else:
            assert payload == install.server(install.PLACEHOLDERS[language])
