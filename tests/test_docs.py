# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The documentation cannot drift from the code, nor one language from another."""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree  # noqa: S405  # nosec B405 - reads what docsgen drew

import pytest

from docsgen import demo, pages

CONTENT = pages.CONTENT
COMPONENTS = CONTENT.parents[1] / "components"
TRANSLATED = ("fr", "es", "de", "nl")
REGENERATE = "run `uv run python -m docsgen` and commit the result"
SVG = "{http://www.w3.org/2000/svg}"


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


@pytest.fixture(scope="module", name="demo_card")
def fixture_demo_card() -> demo.Card:
    """The conversation of the animated demo, played once for the tests that read it."""
    return demo.card()


def test_the_demo_answers_from_four_reads_made_at_the_same_time(demo_card: demo.Card) -> None:
    """Every figure of the answer comes from one of the four calls, sent in one go."""
    assert demo_card.headline == "Restaurants is the only category over budget this month."
    assert (demo_card.over.spent, demo_card.over.budgeted) == (166.50, 120.00)
    assert (demo_card.over.utilization, demo_card.over.available) == (138.8, -22.50)
    assert demo_card.over.trend == (113.70, 119.90, 166.50)
    assert demo_card.room == (("Tennis", 80.00), ("Groceries", 411.90))
    assert demo_card.requests == 7


def test_the_demo_offers_to_cover_what_is_over_and_no_more(demo_card: demo.Card) -> None:
    """The amount proposed is the category's own shortfall, so nothing is set aside idle."""
    assert demo_card.offer.amount == -demo_card.over.available
    assert demo_card.preview.question == "Move 22.50 from Tennis to Restaurants for this month?"
    source, covered = demo_card.preview.sides
    assert (source.name, source.before, source.after) == ("Tennis", 80.00, 57.50)
    assert (covered.name, covered.before, covered.after) == ("Restaurants", 120.00, 142.50)
    assert (covered.available_before, covered.available_after) == (-22.50, 0.00)


def test_the_demo_draws_the_available_amount_only_where_it_differs(
    demo_card: demo.Card,
) -> None:
    """Repeating the budget as the available amount would say nothing: Tennis has spent none."""
    source, covered = demo_card.preview.sides
    assert not source.shifts
    assert covered.shifts


def test_the_demo_says_the_source_has_nothing_spent_only_when_it_has_not(
    demo_card: demo.Card,
) -> None:
    """The sentence offering to cover rests on what the plan says the category spent."""
    assert demo_card.offer.source_spent == 0.0
    assert "nothing spent yet" in demo.picture(demo_card, "light")


def test_the_demo_names_no_date(demo_card: demo.Card) -> None:
    """A date would make the picture look old: the month it works on is "this month"."""
    drawn = demo.picture(demo_card, "light")
    assert "2026-" not in drawn
    assert "this month" in drawn


def test_the_demo_plays_for_thirty_seconds_and_holds_still_when_asked_to(
    demo_card: demo.Card,
) -> None:
    """Each part appears in its own second of a thirty-second loop, unless motion is refused."""
    drawn = demo.picture(demo_card, "light")
    assert drawn.count("30s linear infinite") == 12 + len(demo.LANDS)
    assert "@media (prefers-reduced-motion: reduce)" in drawn
    assert "animation: none" in drawn


def _spans(drawn: str, share: float | None = None) -> list[tuple[str, float, float, float]]:
    """Where every string of a card is drawn, as the generator estimates its width.

    Args:
        drawn: An SVG document.
        share: The average character width to measure with, as a share of the font size;
            None to take the one the string is drawn with.

    Returns:
        One tuple per string, in the order they are drawn: the string, the ordinate of
        its baseline, and the abscissas of its left and right edges.
    """
    spans = []
    root = ElementTree.fromstring(drawn)  # noqa: S314  # nosec B314 - drawn here, not read in
    for node in root.iter(f"{SVG}text"):
        text, size = node.text or "", float(node.get("font-size", "0"))
        drawn_with = demo.FIXED if node.get("font-family") == demo.MONO else demo.SANS
        width = demo.text_width(text, size, drawn_with if share is None else share)
        anchor, x = node.get("text-anchor", "start"), float(node.get("x", "0"))
        left = {"start": x, "middle": x - width / 2, "end": x - width}[anchor]
        spans.append((text, float(node.get("y", "0")), left, left + width))
    return spans


def _overflowing(drawn: str) -> list[str]:
    """Every string of a card that would be drawn past one of its edges.

    Args:
        drawn: An SVG document.

    Returns:
        The strings that do not fit, in the order they are drawn.
    """
    return [
        text
        for text, _, left, right in _spans(drawn)
        if left < demo.MARGIN - 1 or right > demo.WIDTH - demo.MARGIN + 1
    ]


@pytest.mark.parametrize("scheme", ("light", "dark"))
def test_every_line_of_the_demo_fits_inside_the_card(demo_card: demo.Card, scheme: str) -> None:
    """SVG text neither wraps nor shrinks: a longer message would run off the card."""
    over = _overflowing(demo.picture(demo_card, scheme))
    assert not over, f"drawn past the edge of the card: {over}"


@pytest.mark.parametrize("scheme", ("light", "dark"))
def test_the_preview_keeps_its_label_off_the_amount(demo_card: demo.Card, scheme: str) -> None:
    """Each line of the preview leaves the label clear of the budget it labels.

    Measured with the widest character width the card knows, since the average one
    reads these labels and amounts narrower than the font draws them.
    """
    spans = _spans(demo.picture(demo_card, scheme), demo.FIXED)
    labelled = [
        (span, next(beside for beside in spans[index + 1 :] if beside[1] == span[1]))
        for index, span in enumerate(spans)
        if span[0] == "Budgeted"
    ]
    assert len(labelled) == len(demo_card.preview.sides)
    touching = [amount[0] for label, amount in labelled if label[3] > amount[2]]
    assert not touching, f"the label runs into the amount beside it: {touching}"


def test_the_site_shows_the_demo_at_the_size_it_was_drawn(demo_card: demo.Card) -> None:
    """Sizes left behind would stretch the picture: the home pages declare the SVG's own."""
    picture = demo.picture(demo_card, "light")
    drawn = ElementTree.fromstring(picture)  # noqa: S314  # nosec B314 - drawn here, not read in
    component = (COMPONENTS / "WriteDemo.astro").read_text(encoding="utf-8")
    assert (
        re.findall(r'width="(\d+)" height="(\d+)"', component)
        == [(drawn.get("width"), drawn.get("height"))] * 2
    )


@pytest.mark.parametrize("language", ("", *TRANSLATED))
def test_every_home_page_shows_the_demo_with_its_own_alternative_text(language: str) -> None:
    """The demo is on every home page, and each language names what it shows."""
    assert "<WriteDemo />" in (CONTENT / language / "index.mdx").read_text(encoding="utf-8")
    labels = (COMPONENTS / "home-i18n.ts").read_text(encoding="utf-8")
    assert labels.count("writeDemo:") == 1 + len(TRANSLATED)


@pytest.mark.parametrize("language", ("", *TRANSLATED))
def test_every_home_page_shows_the_tour_with_its_own_caption(language: str) -> None:
    """The 20-second tour is on every home page, and each language says what it shows."""
    assert "<Tour />" in (CONTENT / language / "index.mdx").read_text(encoding="utf-8")
    labels = (COMPONENTS / "home-i18n.ts").read_text(encoding="utf-8")
    assert labels.count("tour:") == 1 + len(TRANSLATED)


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


_SITE_LINK = re.compile(r"https://avenir-mcp\.pages\.dev/avenir-mcp/([^\s)>#\"']*)")


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
    r"https://(?:github\.com/mathbeal/avenir-mcp/(?:blob|tree)"
    r"|raw\.githubusercontent\.com/mathbeal/avenir-mcp)/main/([^\s)>\"`#?]+)"
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


_WORKFLOW_BADGE = re.compile(r"actions/workflows/([^/\s)]+\.yml)/badge\.svg")


def test_every_workflow_badge_of_the_readme_shows_a_workflow_that_exists() -> None:
    """A badge of the README names a workflow file of this checkout.

    GitHub answers a badge for a workflow it does not have: it reads "no status",
    grey, instead of going red, so a renamed workflow would leave a badge that
    promises a check nothing runs any more.
    """
    root = CONTENT.parents[3]
    readme = (root / "README.md").read_text(encoding="utf-8")
    badges = _WORKFLOW_BADGE.findall(readme)
    missing = [name for name in badges if not (root / ".github" / "workflows" / name).is_file()]
    assert badges and not missing, f"badges of no workflow: {missing}"


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


_WORDS = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen"}


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
