# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The animated demo of the README and the home pages: one conversation, drawn.

A chat card on the invented demo plan. The user asks how the month is going, the agent
calls four read-only tools at the same time, says what it is waiting for while they come
back, answers with a budget bar, three months of spending and what room is left, offers
to cover exactly what the category is over, and previews the move once the user agrees.
Nothing is applied: the card stops on the preview.

Every figure is replayed by `python -m docsgen`, so the card shows what avenir-mcp
answers today and the test of generated files fails when one of them changes. The amount
the agent offers to move is the category's own negative balance, and the preview's rows,
amounts and available figures are the fields `move_money` returns. Written here, and
nowhere else: the two sentences the user says, the line the agent says while it waits,
the sentence offering to cover, and the labels that name each tool in plain words.

The four calls are made with `asyncio.gather`, and the requests they cost are counted on
the fake YNAB of the demo plan, between the moment they are sent and the moment all four
have answered: the figure is measured, not written.

One SVG per colour scheme. Each part appears in turn over the first ten seconds, each
tool answering in its own: the card then holds complete until the loop starts again, so
the last frame tells the whole story, which is also what a reader who asked their system
for less motion sees, since `prefers-reduced-motion` turns the animation off.
"""

from __future__ import annotations

import asyncio
import html
from dataclasses import dataclass
from typing import Any

from fastmcp import Client

from avenir_mcp.confirm import ONLY_THE_USER
from docsgen import examples, readme

WIDTH = 720
MARGIN = 28
FONT = readme.FONT
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# How wide a character draws, as a share of the font size: SVG text does not wrap or
# measure itself, so every bubble, pill and card is drawn around its text.
SANS, FIXED = 0.47, 0.6

# The cycle and when each part appears in it: the question, the four tools on their way,
# the three parts of what the agent says while it waits, each tool's answer landing, the
# card it builds, the user agreeing, and the preview that changes nothing.
CYCLE, FADE, HOLD = 30.0, 0.6, 29.0
ASKS, SENDS = 0.3, 1.1
TYPES = (1.6, 2.2, 2.8)
LANDS = (2.6, 3.2, 3.8, 4.4)
SHOWS, AGREES, SUGGESTS = 5.2, 7.4, 8.2

MONTH = "2026-09-01"

# The four read-only calls, each with the words the card puts on it, and the write it
# previews. The move's amount is what the plan says the category is over.
READS = (
    ("Month summary", "get_monthly_summary", {"plan_id": examples.BUDGET, "month": MONTH}),
    ("Every category", "get_category_balances", {"plan_id": examples.BUDGET, "month": MONTH}),
    ("Budget vs spent", "get_budget_vs_actual", {"plan_id": examples.BUDGET, "month": MONTH}),
    ("Three months", "get_spending_trends", {"plan_id": examples.BUDGET, "months_count": 3}),
)
MOVE = {
    "plan_id": examples.BUDGET,
    "month": MONTH,
    "from_category_id": "cat-tennis",
    "to_category_id": "cat-restaurants",
}

# What the user says, and what the agent says while the four calls come back, in the
# three parts it is typed in.
ASKED = "Restaurants looks tight. How is the month going, and where is the room?"
AGREED = "Cover it from Tennis."
TYPED = (
    "Looking at the month, every category,",
    " budget against spending",
    " and the last three months…",
)

# The header of the card, and the one line under it.
TITLE, TAGLINE = "avenir-mcp", "your YNAB plan, with an assistant"
NOTE = "Real answers from avenir-mcp on an invented demo plan."

# A preview's message wraps its question in instructions for the agent (confirm.py).
_ASKS = f"Nothing changed yet. {ONLY_THE_USER} "
_AGREE = " If they agree, call again with this code."

# Beyond the charts' palette: the voice of each speaker, and what reads as over budget,
# as still free, and as waiting for a yes.
TONES = {
    "light": {
        "card": "#ffffff",
        "band": "#f3f3f8",
        "panel": "#fbfbfa",
        "line": "#e6e5e0",
        "ink": "#111111",
        "muted": "#5b5b5b",
        "user": "#4f46e5",
        "agent": "#d4522f",
        "good": "#15803d",
        "goodfill": "#eaf6ee",
        "goodline": "#cfe7d8",
        "bad": "#c81e1e",
        "warn": "#e8930c",
        "previewline": "#f0a63a",
        "previewband": "#fdf5ea",
    },
    "dark": {
        "card": "#1a1a19",
        "band": "#232322",
        "panel": "#212120",
        "line": "#383835",
        "ink": "#ffffff",
        "muted": "#c3c2b7",
        "user": "#6f67ef",
        "agent": "#e2694a",
        "good": "#4ade80",
        "goodfill": "#1b3325",
        "goodline": "#2f5c40",
        "bad": "#f87171",
        "warn": "#fbbf24",
        "previewline": "#b9762a",
        "previewband": "#2a2117",
    },
}


@dataclass(frozen=True)
class Side:
    """One side of the move, as `move_money` describes it."""

    name: str
    before: float
    after: float
    available_before: float
    available_after: float

    @property
    def shifts(self) -> bool:
        """Whether the available amount differs from the budget, and so is worth drawing."""
        return self.available_before != self.before


@dataclass(frozen=True)
class Over:
    """The category the month went past, as the four reads describe it."""

    category: str
    budgeted: float
    spent: float
    utilization: float
    available: float
    trend: tuple[float, ...]


@dataclass(frozen=True)
class Offer:
    """What the agent offers to move, and where it offers to take it from."""

    amount: float
    source: str
    source_spent: float


@dataclass(frozen=True)
class Preview:
    """The write the user agrees to, as `move_money` previews it."""

    question: str
    sides: tuple[Side, ...]


@dataclass(frozen=True)
class Card:
    """What the demo draws, once the conversation has been replayed on the demo plan."""

    requests: int
    headline: str
    over: Over
    room: tuple[tuple[str, float], ...]
    offer: Offer
    preview: Preview


@dataclass(frozen=True)
class Played:
    """What the conversation returned, as the tools returned it."""

    summary: dict[str, Any]
    balances: list[dict[str, Any]]
    actual: list[dict[str, Any]]
    trends: dict[str, Any]
    requests: int
    preview: dict[str, Any]


async def _play(amount: float) -> Played:
    """Read the month four ways at once, then preview covering what is over.

    Args:
        amount: What the move asks for, in currency units.

    Returns:
        The four answers, the requests those calls cost, and the preview of the move.
    """
    from avenir_mcp import client, server  # pylint: disable=import-outside-toplevel
    from evals import fake_ynab  # pylint: disable=import-outside-toplevel

    server.configure(enable_writes=True)
    client.PACE.reset()
    async with Client(server.mcp) as mcp_client:

        async def call(tool: str, args: dict[str, Any]) -> dict[str, Any]:
            result = await mcp_client.call_tool(tool, args)
            return result.structured_content or {}

        sent = fake_ynab.STATE.requests
        summary, balances, actual, trends = await asyncio.gather(
            *(call(tool, args) for _, tool, args in READS)
        )
        requests = fake_ynab.STATE.requests - sent
        preview = await call("move_money", {**MOVE, "amount": amount})
    return Played(summary, balances["result"], actual["result"], trends, requests, preview)


def _amount(value: float) -> str:
    """Write an amount the way a tool of avenir-mcp writes it.

    Args:
        value: An amount in currency units.

    Returns:
        E.g. "1,729.32", with a true minus sign when it is negative.
    """
    return f"{value:,.2f}".replace("-", "−")


def _side(side: dict[str, Any]) -> Side:
    """One side of the move, from the fields `move_money` returns for it.

    Args:
        side: The `from_category` or `to_category` of a preview.

    Returns:
        Its name, its budget before and after, and its available amount before and after.
    """
    return Side(
        name=side["name"],
        before=side["from_amount"],
        after=side["to_amount"],
        available_before=side["available_before"],
        available_after=side["available_after"],
    )


def _question(preview: dict[str, Any]) -> str:
    """The first line of the preview's question, with the month named "this month".

    Args:
        preview: A "confirmation_required" answer of `move_money`.

    Returns:
        E.g. "Move 22.50 from Tennis to Restaurants for this month?".
    """
    message: str = preview["message"]
    asked = message.removeprefix(_ASKS).removesuffix(_AGREE)
    return asked.replace(MONTH, "this month").splitlines()[0]


def card() -> Card:
    """Play the conversation against a fresh demo plan and keep what the card draws.

    What the agent offers to move is read from the plan first: it is what the overspent
    category's balance is short of zero, so the preview covers it exactly and no more.

    Returns:
        Every figure the card draws, and the requests the four calls cost.
    """
    over = examples.on_demo_plan(lambda: _play(0.01)).summary["overspent"][0]
    played = examples.on_demo_plan(lambda: _play(-over["balance"]))
    overspent = played.summary["overspent"][0]
    row = next(c for c in played.actual if c["id"] == overspent["category_id"])
    source = next(c for c in played.actual if c["id"] == MOVE["from_category_id"])
    # Beside what the move takes from, the category of the same group with the most left:
    # money set aside for later is not room to spend this month.
    free = max(
        (
            c
            for c in played.balances
            if c["group"] == overspent["group"]
            and c["category_id"] not in {source["id"], overspent["category_id"]}
        ),
        key=lambda c: c["balance"],
    )
    return Card(
        requests=played.requests,
        headline=f"{overspent['name']} is the only category over budget this month.",
        over=Over(
            category=overspent["name"],
            budgeted=row["budgeted"],
            spent=row["actual"],
            utilization=row["utilization_pct"],
            available=overspent["balance"],
            trend=tuple(month["amount"] for month in played.trends[overspent["name"]]),
        ),
        room=((source["name"], source["balance"]), (free["name"], free["balance"])),
        offer=Offer(
            amount=-overspent["balance"],
            source=source["name"],
            source_spent=source["actual"],
        ),
        preview=Preview(
            question=_question(played.preview),
            sides=(
                _side(played.preview["from_category"]),
                _side(played.preview["to_category"]),
            ),
        ),
    )


def text_width(text: str, size: float, per_character: float) -> float:
    """Guess how wide a string draws, to size a bubble or place a label.

    Args:
        text: The string.
        size: Its font size.
        per_character: Its font's average character width, as a share of the size.

    Returns:
        A width in pixels.
    """
    return len(text) * size * per_character


def _text(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    content: str,
    x: float,
    y: float,
    colour: str,
    size: float = 13,
    weight: str = "400",
    anchor: str = "start",
    style: str = "",
    mono: bool = False,
) -> str:
    """One line of text, since every label of the card is drawn the same way.

    Args:
        content: What it says.
        x: Where it starts, is centred or ends, following `anchor`.
        y: Its baseline.
        colour: Its fill.
        size: Its font size.
        weight: Its font weight.
        anchor: "start", "middle" or "end".
        style: "italic" for the line the agent types.
        mono: Whether it is drawn in the monospaced font.

    Returns:
        The element.
    """
    family = f' font-family="{MONO}"' if mono else ""
    slant = f' font-style="{style}"' if style else ""
    place = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size:g}" font-weight="{weight}"'
        f'{family}{slant}{place} fill="{colour}">{html.escape(content)}</text>'
    )


def _style(times: tuple[float, ...]) -> list[str]:
    """One animation per part: appear at its own second, hold, fade back.

    A tool's ring waits from the moment the four calls are sent until its own answer
    lands, where the tick of the same number takes over.

    Args:
        times: When each part appears, in seconds of the cycle.

    Returns:
        The style element's lines.
    """
    rules = []
    for index, second in enumerate(times):
        rules.append(f".p{index} {{ animation: a{index} {CYCLE:.0f}s linear infinite }}")
        rules.append(
            f"@keyframes a{index} {{ 0%, {second / CYCLE * 100:.1f}% {{ opacity: 0 }} "
            f"{(second + FADE) / CYCLE * 100:.1f}%, {HOLD / CYCLE * 100:.1f}% "
            "{ opacity: 1 } 100% { opacity: 0 } }"
        )
    for index, second in enumerate(LANDS):
        rules.append(f".w{index} {{ animation: w{index} {CYCLE:.0f}s linear infinite }}")
        rules.append(
            f"@keyframes w{index} {{ 0%, {SENDS / CYCLE * 100:.1f}% {{ opacity: 0 }} "
            f"{(SENDS + FADE) / CYCLE * 100:.1f}%, {second / CYCLE * 100:.1f}% "
            f"{{ opacity: 1 }} {(second + FADE) / CYCLE * 100:.1f}%, 100% {{ opacity: 0 }} }}"
        )
    quiet = ", ".join(
        [*(f".p{index}" for index in range(len(times))), *(f".w{index}" for index in range(4))]
    )
    rules.append(f"@media (prefers-reduced-motion: reduce) {{ {quiet} {{ animation: none }} }}")
    rules.append("@media (prefers-reduced-motion: reduce) { .wait { opacity: 0 } }")
    return ["<style>", *rules, "</style>"]


def _header(tone: dict[str, str]) -> list[str]:
    """The band at the top: who is speaking, and what the card is.

    Args:
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    return [
        f'<path d="M0.5 12.5a12 12 0 0 1 12-12h695a12 12 0 0 1 12 12V56H0.5Z" '
        f'fill="{tone["band"]}"/>',
        f'<circle cx="{MARGIN + 14}" cy="28" r="14" fill="{tone["user"]}"/>',
        _text("a", MARGIN + 14, 33, "#ffffff", 14, "700", "middle"),
        _text(TITLE, MARGIN + 36, 33, tone["ink"], 15, "700"),
        _text(TAGLINE, WIDTH - MARGIN, 33, tone["muted"], 12.5, "400", "end"),
    ]


def _bubble(said: str, top: float, part: int, tone: dict[str, str]) -> tuple[list[str], float]:
    """What the user says: a bubble on the right, with their name beside it.

    Args:
        said: The sentence.
        top: Where the bubble starts.
        part: The part's number, for its animation.
        tone: The scheme's colours.

    Returns:
        The elements, and the ordinate below them.
    """
    height, badge = 38.0, 30.0
    width = min(text_width(said, 13.5, SANS) + 36, WIDTH - 2 * MARGIN - badge - 10)
    right = WIDTH - MARGIN - badge - 10
    left = right - width
    middle = right + 10 + badge / 2
    return (
        [
            f'<g class="p{part}">',
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{height}" '
            f'rx="{height / 2}" fill="{tone["user"]}"/>',
            _text(said, left + width / 2, top + 24, "#ffffff", 13.5, "600", "middle"),
            f'<circle cx="{middle:.1f}" cy="{top + height / 2:.1f}" r="{badge / 2}" '
            f'fill="{tone["band"]}" stroke="{tone["line"]}"/>',
            _text("You", middle, top + height / 2 + 4, tone["muted"], 10.5, "600", "middle"),
            "</g>",
        ],
        top + height + 14,
    )


def _avatar(top: float, part: int, tone: dict[str, str]) -> list[str]:
    """The assistant's mark, beside what it says.

    Args:
        top: Where the line it belongs to starts.
        part: The part's number, for its animation.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    return [
        f'<g class="p{part}">',
        f'<circle cx="{MARGIN + 14}" cy="{top + 14:.1f}" r="14" fill="{tone["agent"]}"/>',
        _text("✳", MARGIN + 14, top + 20, "#ffffff", 15, "700", "middle"),
        "</g>",
    ]


def _typed(top: float, tone: dict[str, str]) -> list[str]:
    """The line the agent types while the four calls come back, part by part.

    Args:
        top: Where the line starts.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    spans = "".join(
        f'<tspan class="p{index + 2}">{html.escape(chunk)}</tspan>'
        for index, chunk in enumerate(TYPED)
    )
    return [
        f'<text x="{MARGIN + 36}" y="{top + 18:.1f}" font-size="13" font-style="italic" '
        f'fill="{tone["muted"]}">{spans}</text>'
    ]


def _tools(top: float, tone: dict[str, str]) -> list[str]:
    """The four calls, side by side: each waits, then shows its answer has come back.

    Args:
        top: Where the row starts.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    parts: list[str] = []
    gap, height = 8.0, 46.0
    width = (WIDTH - 2 * MARGIN - 3 * gap) / 4
    for index, (label, tool, _) in enumerate(READS):
        left = MARGIN + index * (width + gap)
        mark = left + 20
        parts += [
            '<g class="p1">',
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{height}" '
            f'rx="10" fill="{tone["goodfill"]}" stroke="{tone["goodline"]}"/>',
            _text(label, left + 34, top + 20, tone["ink"], 12.5, "700"),
            _text(tool, left + 34, top + 36, tone["muted"], 9, "400", mono=True),
            "</g>",
            f'<g class="w{index} wait">',
            f'<circle cx="{mark:.1f}" cy="{top + 23:.1f}" r="7" fill="none" '
            f'stroke="{tone["goodline"]}" stroke-width="2.5" stroke-dasharray="11 33" '
            'stroke-linecap="round"/>',
            "</g>",
            f'<g class="p{index + 5}">',
            f'<circle cx="{mark:.1f}" cy="{top + 23:.1f}" r="8" fill="{tone["good"]}"/>',
            f'<path d="M{mark - 3.6:.1f} {top + 23:.1f}l2.6 2.8 4.6-5.4" fill="none" '
            'stroke="#ffffff" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"/>',
            "</g>",
        ]
    return parts


def _bar(shown: Card, left: float, top: float, width: float, tone: dict[str, str]) -> list[str]:
    """The budget bar: what was spent, where the budget ends, and what is left available.

    Args:
        shown: What the conversation returned.
        left: Where the bar starts.
        top: Where the bar's row starts.
        width: How wide the bar is.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    share = min(100.0 / shown.over.utilization, 1.0) if shown.over.utilization else 1.0
    marker = left + width * share
    return [
        _text(shown.over.category, left, top, tone["ink"], 13, "600"),
        _text("budget 100 %", marker, top, tone["muted"], 11, "400", "end"),
        f'<rect x="{left:.1f}" y="{top + 10:.1f}" width="{width:.1f}" height="14" rx="7" '
        f'fill="{tone["bad"]}"/>',
        f'<rect x="{left:.1f}" y="{top + 10:.1f}" width="{marker - left:.1f}" height="14" '
        f'rx="7" fill="{tone["warn"]}"/>',
        f'<line x1="{marker:.1f}" y1="{top + 6:.1f}" x2="{marker:.1f}" y2="{top + 28:.1f}" '
        f'stroke="{tone["ink"]}" stroke-width="1.5" stroke-dasharray="3 3"/>',
        _text(
            f"{_amount(shown.over.spent)} spent of {_amount(shown.over.budgeted)} budgeted",
            left,
            top + 44,
            tone["ink"],
            12.5,
        ),
        _text(
            f"{shown.over.utilization:g} % · available {_amount(shown.over.available)}",
            left + width,
            top + 44,
            tone["bad"],
            12.5,
            "700",
            "end",
        ),
    ]


def _points(
    trend: tuple[float, ...], left: float, top: float, width: float
) -> list[tuple[float, float]]:
    """Where each month of the trend is drawn, the lowest month sitting on the baseline.

    Args:
        trend: What was spent each month.
        left: Where the row starts.
        top: Where the row starts.
        width: How wide the row is.

    Returns:
        One point per month.
    """
    low, high = min(trend), max(trend)
    span = high - low or 1.0
    height, inset = 34.0, 180.0
    return [
        (
            left + inset + index * (width - inset - 70) / (len(trend) - 1),
            top + 10 + height - (value - low) / span * height,
        )
        for index, value in enumerate(trend)
    ]


def _point(x: float, y: float, value: float, last: bool, tone: dict[str, str]) -> list[str]:
    """One month of the trend: its point, and the amount written beside it.

    Args:
        x: Where the point goes.
        y: Where the point goes.
        value: What was spent that month.
        last: Whether it is this month, which the card calls out.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    return [
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" '
        f'fill="{tone["bad"] if last else tone["card"]}" stroke="{tone["bad"]}" '
        'stroke-width="2"/>',
        _text(
            _amount(value),
            x + (12 if last else 0),
            y + (5 if last else 20),
            tone["bad"] if last else tone["muted"],
            11.5,
            "700" if last else "400",
            "start" if last else "middle",
        ),
    ]


def _trend(shown: Card, left: float, top: float, width: float, tone: dict[str, str]) -> list[str]:
    """Three months of spending, drawn, each month's amount written beside its point.

    Args:
        shown: What the conversation returned.
        left: Where the row starts.
        top: Where the row starts.
        width: How wide the row is.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    points = _points(shown.over.trend, left, top, width)
    marks = []
    for index, ((x, y), value) in enumerate(zip(points, shown.over.trend, strict=True)):
        marks += _point(x, y, value, index == len(points) - 1, tone)
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return [
        _text("Spending, last three months", left, top + 32, tone["ink"], 12.5),
        f'<polyline points="{line}" fill="none" stroke="{tone["bad"]}" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/>',
        *marks,
    ]


def _room(shown: Card, left: float, top: float, tone: dict[str, str]) -> list[str]:
    """What is still free, as one pill per category.

    Args:
        shown: What the conversation returned.
        left: Where the row starts.
        top: Where the row starts.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    parts = [_text("Room left", left, top + 19, tone["ink"], 12.5)]
    at = left + 76
    for name, value in shown.room:
        said = f"{name} {_amount(value)}"
        width = text_width(said, 12, SANS) + 26
        parts += [
            f'<rect x="{at:.1f}" y="{top:.1f}" width="{width:.1f}" height="28" rx="14" '
            f'fill="{tone["goodfill"]}" stroke="{tone["goodline"]}"/>',
            _text(said, at + width / 2, top + 19, tone["good"], 12, "600", "middle"),
        ]
        at += width + 8
    return parts


def _answer(shown: Card, top: float, tone: dict[str, str]) -> tuple[list[str], float]:
    """The panel the agent answers with: the bar, the trend, the room, the offer.

    Args:
        shown: What the conversation returned.
        top: Where the panel starts.
        tone: The scheme's colours.

    Returns:
        The elements, and the ordinate below the panel.
    """
    left = MARGIN + 36.0
    width = WIDTH - MARGIN - left
    inner = left + 20
    content = width - 40
    height = 268.0
    spent = "nothing spent yet" if not shown.offer.source_spent else "the most room left"
    return (
        [
            '<g class="p9">',
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{height}" '
            f'rx="14" fill="{tone["panel"]}" stroke="{tone["line"]}"/>',
            _text(shown.headline, inner, top + 30, tone["ink"], 14.5, "700"),
            *_bar(shown, inner, top + 58, content, tone),
            *_trend(shown, inner, top + 112, content, tone),
            *_room(shown, inner, top + 192, tone),
            _text(
                f"I can cover the {_amount(shown.offer.amount)} from "
                f"{shown.offer.source}, which has {spent}.",
                inner,
                top + 244,
                tone["ink"],
                12.5,
            ),
            "</g>",
        ],
        top + height + 16,
    )


def _rows(shown: Card, inner: float, top: float, tone: dict[str, str]) -> list[str]:
    """One line per side of the move: its budget before and after, then what it leaves.

    Args:
        shown: What the conversation returned.
        inner: Where a line starts.
        top: Where the first line's baseline goes.
        tone: The scheme's colours.

    Returns:
        The elements.
    """
    rows = []
    for index, side in enumerate(shown.preview.sides):
        line = top + index * 30
        rows += [
            _text(side.name, inner, line, tone["ink"], 12.5),
            _text(_amount(side.before), inner + 190, line, tone["muted"], 12.5, "400", "end"),
            _text("→", inner + 200, line, tone["muted"], 12.5),
            _text(_amount(side.after), inner + 218, line, tone["ink"], 12.5, "700"),
        ]
        if side.shifts:
            rows += [
                _text("available", inner + 296, line, tone["muted"], 12),
                _text(_amount(side.available_before), inner + 360, line, tone["bad"], 12.5, "700"),
                _text("→", inner + 418, line, tone["muted"], 12.5),
                _text(_amount(side.available_after), inner + 436, line, tone["good"], 12.5, "700"),
            ]
    return rows


def _preview(shown: Card, top: float, tone: dict[str, str]) -> tuple[list[str], float]:
    """The preview: what each side becomes, what it leaves available, and the two buttons.

    Args:
        shown: What the conversation returned.
        top: Where the card starts.
        tone: The scheme's colours.

    Returns:
        The elements, and the ordinate below the card.
    """
    left = MARGIN + 36.0
    width = WIDTH - MARGIN - left
    inner = left + 20
    content = width - 40
    height = 200.0
    buttons = top + height - 40
    return (
        [
            '<g class="p11">',
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{height}" '
            f'rx="14" fill="{tone["card"]}" stroke="{tone["previewline"]}"/>',
            f'<path d="M{left:.1f} {top + 14:.1f}a14 14 0 0 1 14-14h{width - 28:.1f}'
            f'a14 14 0 0 1 14 14V{top + 48:.1f}H{left:.1f}Z" fill="{tone["previewband"]}"/>',
            _text(shown.preview.question, inner, top + 31, tone["agent"], 13.5, "700"),
            _text(
                "move_money · preview",
                left + width - 20,
                top + 31,
                tone["muted"],
                10.5,
                "400",
                "end",
                mono=True,
            ),
            *_rows(shown, inner, top + 80, tone),
            f'<rect x="{inner:.1f}" y="{top + 124:.1f}" width="{content:.1f}" height="10" '
            f'rx="5" fill="{tone["good"]}"/>',
            _text(
                "exactly on budget",
                inner + content,
                top + 152,
                tone["good"],
                11.5,
                "700",
                "end",
            ),
            _text(
                "Nothing changes until you confirm · undo anytime",
                inner,
                buttons + 20,
                tone["muted"],
                11.5,
            ),
            f'<rect x="{inner + content - 196:.1f}" y="{buttons:.1f}" width="90" height="30" '
            f'rx="8" fill="{tone["card"]}" stroke="{tone["line"]}"/>',
            _text(
                "Cancel", inner + content - 151, buttons + 20, tone["ink"], 12.5, "600", "middle"
            ),
            f'<rect x="{inner + content - 96:.1f}" y="{buttons:.1f}" width="96" height="30" '
            f'rx="8" fill="{tone["user"]}"/>',
            _text("Confirm", inner + content - 48, buttons + 20, "#ffffff", 12.5, "700", "middle"),
            "</g>",
        ],
        top + height + 14,
    )


def _body(shown: Card, tone: dict[str, str]) -> tuple[list[str], float]:
    """Stack the conversation down the card, each part in the order it appears.

    Args:
        shown: What the conversation returned.
        tone: The scheme's colours.

    Returns:
        The elements, and the ordinate below the last part.
    """
    parts = list(_header(tone))
    top = 72.0
    asked, top = _bubble(ASKED, top, 0, tone)
    parts += asked
    parts += _avatar(top, 1, tone)
    parts += _typed(top, tone)
    top += 34
    parts += _tools(top, tone)
    top += 58
    answer, top = _answer(shown, top, tone)
    parts += answer
    agreed, top = _bubble(AGREED, top, 10, tone)
    parts += agreed
    parts += _avatar(top, 11, tone)
    preview, top = _preview(shown, top, tone)
    parts += preview
    return parts, top


def picture(shown: Card, scheme: str) -> str:
    """Draw the conversation as an SVG that plays it part by part.

    Args:
        shown: What the conversation returned, from :func:`card`.
        scheme: "light" or "dark".

    Returns:
        The SVG document.
    """
    tone = TONES[scheme]
    times = (ASKS, SENDS, *TYPES, *LANDS, SHOWS, AGREES, SUGGESTS)
    parts, bottom = _body(shown, tone)
    height = bottom + 24
    told = " ".join(
        (
            ASKED,
            "".join(TYPED),
            shown.headline,
            f"{_amount(shown.over.spent)} spent of {_amount(shown.over.budgeted)} budgeted, "
            f"{shown.over.utilization:g} %, available {_amount(shown.over.available)}.",
            AGREED,
            shown.preview.question,
        )
    )
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height:.0f}" '
            f'viewBox="0 0 {WIDTH} {height:.0f}" font-family="{FONT}" role="img" '
            'aria-labelledby="title desc">',
            '<title id="title">A conversation with avenir-mcp: four reads at once, '
            "then a previewed move</title>",
            f'<desc id="desc">{html.escape(told)}</desc>',
            *_style(times),
            f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1:.0f}" rx="12" '
            f'fill="{tone["card"]}" stroke="{tone["line"]}"/>',
            *parts,
            _text(NOTE, WIDTH / 2, height - 12, tone["muted"], 11, "400", "middle"),
            "</svg>",
            "",
        ]
    )


def pictures() -> dict[str, str]:
    """Draw the demo in both colour schemes.

    Returns:
        Each scheme's SVG, by scheme name.
    """
    shown = card()
    return {scheme: picture(shown, scheme) for scheme in readme.SCHEMES}
