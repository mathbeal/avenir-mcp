# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The animated demo of the README and the home pages: one write, from preview to undo.

Three exchanges on the invented demo plan: `move_money` previews a move and changes
nothing, the user agrees and it is applied, `undo_operation` puts both amounts back.
The conversation is replayed when `python -m docsgen` runs, so every answer the card
shows is what avenir-mcp returns today and the test of generated files fails when a
message, an amount or a status changes. Only the three sentences the user says are
written here; the month is written "this month" and the journal id `<operation id>`,
as the documented examples do, so the picture does not age.

One SVG per colour scheme, as the charts are. Each part appears in turn over thirty
seconds and the transcript then holds complete before the loop starts again: the last
frame tells the whole story, which is also what a reader who asked their system for
less motion sees, since `prefers-reduced-motion` turns the animation off.
"""

from __future__ import annotations

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

# Heights of the three parts of an exchange, and of a line of the answer.
BUBBLE, CHIP, LINE = 34, 26, 19

# How wide a character draws, as a share of the font size: SVG text does not wrap or
# measure itself, so a bubble and a chip are drawn around their text.
SANS, FIXED = 0.47, 0.6

# The cycle: one exchange every 9.5 s, its three parts a second apart, everything
# visible from 22.1 s to 29 s, then a fade back to the first frame.
CYCLE, FADE, EVERY, HOLD = 30.0, 0.8, 9.5, 29.0

MONTH = "2026-09-01"
MOVE = {
    "plan_id": examples.BUDGET,
    "month": MONTH,
    "from_category_id": "cat-tennis",
    "to_category_id": "cat-restaurants",
    "amount": 30,
}

# What the user says, and how the card names the call their words lead to.
SAID = (
    ("Restaurants is over budget. Move 30 from Tennis to cover it.", "move_money · preview"),
    ("Yes, go ahead.", "move_money · with the confirmation code"),
    ("Actually, put it back.", "undo_operation · preview, then the code"),
)

# A preview's message wraps its question in instructions for the agent (confirm.py).
_ASKS = f"Nothing changed yet. {ONLY_THE_USER} "
_AGREE = " If they agree, call again with this code."


@dataclass(frozen=True)
class Step:
    """One exchange of the demo: what the user said, the call, and what came back."""

    said: str
    call: str
    status: str
    lines: tuple[str, ...]


async def _play() -> list[dict[str, Any]]:
    """Move money, confirm the move, then undo it, on the demo plan.

    Returns:
        The four answers: the preview, the applied move, the undo's preview, the undo.
    """
    from avenir_mcp import client, server  # pylint: disable=import-outside-toplevel

    server.configure(enable_writes=True)
    client.PACE.reset()
    answers: list[dict[str, Any]] = []
    async with Client(server.mcp) as mcp_client:

        async def call(tool: str, args: dict[str, Any]) -> dict[str, Any]:
            result = await mcp_client.call_tool(tool, args)
            answers.append(result.structured_content or {})
            return answers[-1]

        preview = await call("move_money", MOVE)
        await call("move_money", {**MOVE, "confirmation": preview["confirmation"]})
        undo = await call("undo_operation", {"plan_id": examples.BUDGET})
        await call(
            "undo_operation", {"plan_id": examples.BUDGET, "confirmation": undo["confirmation"]}
        )
    return answers


def _asked(answer: dict[str, Any]) -> tuple[str, ...]:
    """The question a preview puts to the user, without the instructions around it.

    Args:
        answer: A "confirmation_required" answer.

    Returns:
        Its lines, the month named "this month".
    """
    question = answer["message"].removeprefix(_ASKS).removesuffix(_AGREE)
    return tuple(question.replace(MONTH, "this month").splitlines())


def _done(answer: dict[str, Any]) -> str:
    """What an applied answer says, with the journal id of the documented examples.

    Args:
        answer: An "applied" answer.

    Returns:
        Its message, the random operation id replaced by a placeholder.
    """
    message: str = answer["message"]
    operation = answer.get("operation_id")
    return message.replace(operation, "<operation id>") if operation else message


def steps(answers: list[dict[str, Any]]) -> list[Step]:
    """Turn the four answers of the conversation into the three exchanges of the card.

    Args:
        answers: What :func:`capture` returned.

    Returns:
        The preview, the confirmed move, and the undo with its own question.
    """
    preview, applied, undo, undone = answers
    bodies = (_asked(preview), (_done(applied),), (*_asked(undo), _done(undone)))
    outcomes = (preview, applied, undone)
    return [
        Step(said, call, outcome["status"], body)
        for (said, call), outcome, body in zip(SAID, outcomes, bodies, strict=True)
    ]


def capture() -> list[dict[str, Any]]:
    """Play the conversation against a fresh demo plan.

    Returns:
        The four answers, as the tools returned them.
    """
    return examples.on_demo_plan(_play)


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


def _style(times: list[float]) -> list[str]:
    """One animation per part of the card: appear at its own second, hold, fade out.

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
    quiet = ", ".join(f".p{index}" for index in range(len(times)))
    rules.append(f"@media (prefers-reduced-motion: reduce) {{ {quiet} {{ animation: none }} }}")
    return ["<style>", *rules, "</style>"]


def _bubble(said: str, top: float, part: int, colour: dict[str, str]) -> list[str]:
    """Draw what the user says, as a bubble on the right.

    Args:
        said: The sentence.
        top: Where the bubble starts.
        part: The part's number, for its animation.
        colour: The scheme's colours.

    Returns:
        The elements.
    """
    width = min(text_width(said, 14, SANS) + 40, WIDTH - 2 * MARGIN)
    left = WIDTH - MARGIN - width
    return [
        f'<g class="p{part}">',
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{BUBBLE}" '
        f'rx="{BUBBLE / 2}" fill="{colour["end"]}"/>',
        f'<text x="{left + width / 2:.1f}" y="{top + 22:.1f}" font-size="14" font-weight="500" '
        f'text-anchor="middle" fill="#ffffff">{html.escape(said)}</text>',
        "</g>",
    ]


def _call(step: Step, top: float, part: int, colour: dict[str, str]) -> list[str]:
    """Draw the call the agent makes and the status it got back.

    Args:
        step: The exchange.
        top: Where the row starts.
        part: The part's number, for its animation.
        colour: The scheme's colours.

    Returns:
        The elements.
    """
    waiting = step.status == "confirmation_required"
    dot = colour["lowest"] if waiting else colour["end"]
    label = text_width(step.status, 11, FIXED)
    return [
        f'<g class="p{part}">',
        f'<rect x="{MARGIN}" y="{top:.1f}" width="{text_width(step.call, 12, FIXED) + 28:.1f}" '
        f'height="{CHIP}" rx="6" fill="{colour["grid"]}"/>',
        f'<text x="{MARGIN + 14}" y="{top + 17:.1f}" font-size="12" font-family="{MONO}" '
        f'fill="{colour["secondary"]}">{html.escape(step.call)}</text>',
        f'<circle cx="{WIDTH - MARGIN - label - 10:.1f}" cy="{top + 13:.1f}" r="4" fill="{dot}"/>',
        f'<text x="{WIDTH - MARGIN}" y="{top + 17:.1f}" font-size="11" font-family="{MONO}" '
        f'text-anchor="end" fill="{colour["primary"]}">{html.escape(step.status)}</text>',
        "</g>",
    ]


def _answer(step: Step, top: float, part: int, colour: dict[str, str]) -> list[str]:
    """Draw what avenir-mcp answered, behind a rule in the status's colour.

    Args:
        step: The exchange.
        top: Where the answer starts.
        part: The part's number, for its animation.
        colour: The scheme's colours.

    Returns:
        The elements.
    """
    waiting = step.status == "confirmation_required"
    height = len(step.lines) * LINE
    lines = [
        f'<text x="{MARGIN + 16}" y="{top + 14 + index * LINE:.1f}" font-size="13" '
        f'fill="{colour["primary"]}">{html.escape(line)}</text>'
        for index, line in enumerate(step.lines)
    ]
    return [
        f'<g class="p{part}">',
        f'<rect x="{MARGIN}" y="{top:.1f}" width="3" height="{height}" rx="1.5" '
        f'fill="{colour["lowest"] if waiting else colour["end"]}"/>',
        *lines,
        "</g>",
    ]


def _body(shown: list[Step], colour: dict[str, str]) -> tuple[list[str], list[float], float]:
    """Stack the exchanges down the card.

    Args:
        shown: The exchanges.
        colour: The scheme's colours.

    Returns:
        The elements, when each part appears, and the ordinate below the last one.
    """
    parts: list[str] = []
    times: list[float] = []
    top = 54.0
    for index, step in enumerate(shown):
        appears = index * EVERY + 0.3
        times += [appears, appears + 1.0, appears + 2.0]
        parts += _bubble(step.said, top, len(times) - 3, colour)
        top += BUBBLE + 12
        parts += _call(step, top, len(times) - 2, colour)
        top += CHIP + 10
        parts += _answer(step, top, len(times) - 1, colour)
        top += len(step.lines) * LINE + 18
    return parts, times, top


# Under the card: where its figures come from, and the two placeholders. The entities
# are written as they go into the file; the rest of the card's text is escaped.
NOTE = (
    "Every answer above is what avenir-mcp returns on the invented demo plan today, "
    "replayed by python -m docsgen.",
    "“this month” stands for the month’s name, &lt;operation id&gt; for the journal id.",
)


def _footer(top: float, colour: dict[str, str]) -> list[str]:
    """Say what the card shows and what stands in for what.

    Args:
        top: Where the first line's baseline goes.
        colour: The scheme's colours.

    Returns:
        The elements.
    """
    return [
        f'<text x="{MARGIN}" y="{top + index * 16:.1f}" font-size="11" '
        f'fill="{colour["secondary"]}">{line}</text>'
        for index, line in enumerate(NOTE)
    ]


def picture(shown: list[Step], scheme: str) -> str:
    """Draw the demo as an SVG that plays its three exchanges in turn.

    Args:
        shown: The exchanges, from :func:`steps`.
        scheme: "light" or "dark".

    Returns:
        The SVG document.
    """
    colour = readme.SCHEMES[scheme]
    parts, times, bottom = _body(shown, colour)
    height = bottom + 16 * (len(NOTE) - 1) + 14
    told = " ".join(f"{step.said} {' '.join(step.lines)}" for step in shown)
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height:.0f}" '
            f'viewBox="0 0 {WIDTH} {height:.0f}" font-family="{FONT}" role="img" '
            'aria-labelledby="title desc">',
            '<title id="title">One write in avenir-mcp: previewed, confirmed, then undone</title>',
            f'<desc id="desc">{html.escape(told)}</desc>',
            *_style(times),
            f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1:.0f}" rx="12" '
            f'fill="{colour["surface"]}" stroke="{colour["border"]}"/>',
            f'<text x="{MARGIN}" y="36" font-size="12" font-weight="600" '
            f'fill="{colour["secondary"]}">avenir-mcp in Claude Code</text>',
            f'<text x="{WIDTH - MARGIN}" y="36" font-size="12" text-anchor="end" '
            f'fill="{colour["secondary"]}">One write: previewed, confirmed, undone</text>',
            *parts,
            *_footer(bottom, colour),
            "</svg>",
            "",
        ]
    )


def pictures() -> dict[str, str]:
    """Draw the demo in both colour schemes.

    Returns:
        Each scheme's SVG, by scheme name.
    """
    shown = steps(capture())
    return {scheme: picture(shown, scheme) for scheme in readme.SCHEMES}
