# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The documentation cannot drift from the code, nor one language from another."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from docsgen import pages

CONTENT = pages.CONTENT
TRANSLATED = ("fr", "es", "de", "nl")
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
    """Each translation has every hand-written page English has, and no other."""
    generated = {p for p in pages.generated() if p.suffix == ".md"}
    english = _english_pages() - {p.relative_to(CONTENT) for p in generated}
    translated = {
        p.relative_to(CONTENT / language)
        for p in (CONTENT / language).rglob("*.md*")
        if p not in generated
    }
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


def _language_pages(language: str) -> list[Path]:
    """A language's pages: English is the content root, less the translations."""
    pages_ = (CONTENT / language).rglob("*.md*")
    return [p for p in pages_ if language or p.relative_to(CONTENT).parts[0] not in TRANSLATED]


@pytest.mark.parametrize("language", ("", *TRANSLATED))
def test_every_snippet_is_used_by_a_page(language: str) -> None:
    """No example is generated for nothing, in any language."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in _language_pages(language))
    prefix = f"@snippets/{language}/" if language else "@snippets/"
    folder = pages.SNIPPETS / language
    unused = [p.name for p in folder.glob("*.json") if f"{prefix}{p.name}" not in text]
    assert not unused


@pytest.mark.parametrize("language", ("", *TRANSLATED))
def test_a_page_shows_the_examples_of_its_own_language(language: str) -> None:
    """A French page shows the demo budget named in French: its categories match its prose."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in _language_pages(language))
    imported = re.findall(r"@snippets/([^'\"]+)", text)
    prefix = f"{language}/" if language else ""
    assert imported
    assert [name for name in imported if not re.fullmatch(f"{prefix}[^/]+", name)] == []


_SITE_LINK = re.compile(r"https://mathbeal\.github\.io/avenir-mcp/([^\s)>#\"']*)")


def _page_exists(path: str) -> bool:
    stem = CONTENT / path.strip("/") if path.strip("/") else CONTENT / "index"
    candidates = [stem.with_suffix(".md"), stem.with_suffix(".mdx")]
    candidates += [stem / "index.md", stem / "index.mdx"]
    return any(candidate.is_file() for candidate in candidates)


def test_every_link_to_the_site_from_the_repository_reaches_a_page() -> None:
    """A link from the README or another root file to the site names a page that exists.

    The site checks its own links when it builds; nothing checks the ones pointing
    at it from outside, and a page renamed there leaves them on a 404.
    """
    root = CONTENT.parents[3]
    sources = [*sorted(root.glob("*.md")), root / "pyproject.toml"]
    broken = [
        f"{source.name}: {path}"
        for source in sources
        for path in _SITE_LINK.findall(source.read_text(encoding="utf-8"))
        if not _page_exists(path)
    ]
    assert not broken, f"links to no page of the site: {broken}"


_REPOSITORY_FILE = re.compile(
    r"https://github\.com/mathbeal/avenir-mcp/(?:blob|tree)/main/([^\s)>\"`#]+)"
)


def test_every_link_to_a_file_of_the_repository_names_one_that_exists() -> None:
    """A link to a file of the repository on main names a file of this checkout.

    The link check leaves these links out: a pull request that adds a file and links
    to it would otherwise fail until it is merged.
    """
    root = CONTENT.parents[3]
    sources = [*sorted(root.glob("*.md")), *sorted(CONTENT.rglob("*.md*"))]
    broken = [
        f"{source.relative_to(root)}: {path}"
        for source in sources
        for path in _REPOSITORY_FILE.findall(source.read_text(encoding="utf-8"))
        if not (root / path).exists()
    ]
    assert not broken, f"links to no file of the repository: {broken}"


def _install_link(prefix: str) -> str:
    readme = (CONTENT.parents[3] / "README.md").read_text(encoding="utf-8")
    found = re.search(rf"\]\(({re.escape(prefix)}[^)]+)\)", readme)
    assert found, f"no install button linking to {prefix} in the README"
    return found.group(1)


def test_the_vs_code_button_installs_avenir_mcp_and_asks_for_the_token_hidden() -> None:
    """The VS Code button runs uvx avenir-mcp, read-only, the token typed into a password box."""
    query = parse_qs(
        urlsplit(_install_link("https://insiders.vscode.dev/redirect/mcp/install?")).query
    )
    config = json.loads(query["config"][0])
    (token,) = json.loads(query["inputs"][0])
    assert query["name"] == ["avenir-mcp"]
    assert (config["command"], config["args"]) == ("uvx", ["avenir-mcp"])
    assert config["env"] == {"YNAB_API_KEY": f"${{input:{token['id']}}}"}
    assert (token["type"], token["password"]) == ("promptString", True)


def test_the_cursor_button_installs_avenir_mcp_read_only() -> None:
    """The Cursor button runs uvx avenir-mcp without write access, with a token to fill in."""
    query = parse_qs(urlsplit(_install_link("https://cursor.com/en/install-mcp?")).query)
    config = json.loads(base64.b64decode(query["config"][0]))
    assert query["name"] == ["avenir-mcp"]
    assert (config["command"], config["args"]) == ("uvx", ["avenir-mcp"])
    assert config["env"] == {"YNAB_API_KEY": "your-token"}


def _tool_counts() -> tuple[int, int]:
    """How many tools a client lists read-only, and how many writes add."""
    import asyncio  # pylint: disable=import-outside-toplevel

    from avenir_mcp import server  # pylint: disable=import-outside-toplevel

    async def listed(writes: bool) -> int:
        server.configure(enable_writes=writes)
        try:
            return len(await server.mcp.list_tools())
        finally:
            server.configure(enable_writes=False)

    read, every = asyncio.run(listed(False)), asyncio.run(listed(True))
    return read, every - read


_WORDS = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen"}


def test_the_tool_counts_written_in_the_pages_are_the_servers() -> None:
    """Every page that counts the tools says what a client actually lists."""
    read, write = _tool_counts()
    total = read + write
    expected = {
        "getting-started/features.mdx": [f"gives an agent {total} tools"],
        "guides/run-options.mdx": [
            f"{read} read-only tools; the {write} write tools",
            f"all {total} tools",
        ],
        "getting-started/install.mdx": [
            f"`avenir-mcp` shows its {read} tools",
            f"running, with {read}\n    tools",
            f"lists **{total}** tools instead of {read}",
            f"| Tools listed | {read} | {total} |",
        ],
        "guides/choose-a-model.mdx": [f"the right one of {total} tools"],
        "reference/configuration.mdx": [f"registers the {write} write tools"],
        "index.mdx": [f"The {_WORDS[write]} write tools"],
    }
    for page, phrases in expected.items():
        text = (CONTENT / page).read_text(encoding="utf-8")
        for phrase in phrases:
            assert phrase in text, f"{page} should say {phrase!r}"


@pytest.mark.parametrize("language", TRANSLATED)
def test_every_translation_counts_the_same_tools(language: str) -> None:
    """The totals written in each translation are the server's too."""
    read, write = _tool_counts()
    total = read + write
    for page, numbers in {
        "getting-started/features.mdx": [total],
        "guides/run-options.mdx": [read, write, total],
        "guides/choose-a-model.mdx": [total],
        "reference/configuration.mdx": [write],
        "getting-started/install.mdx": [read, total],
    }.items():
        text = (CONTENT / language / page).read_text(encoding="utf-8")
        for number in numbers:
            assert re.search(rf"\b{number}\b", text), f"{language}/{page} lacks {number}"
