# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The charts at the top of the README, drawn from the documented examples.

The forecast is `forecast_balance` on the demo plan (`docs/src/snippets/forecast.json`),
the net worth `get_net_worth_trend` on the same plan (`docs/src/snippets/net_worth.json`),
so each chart shows what its tool answers today, and the test of generated files fails
when it no longer does. One SVG per colour scheme: GitHub picks it with `<picture>`.
Colours are the reference palette's first two categorical slots, checked for
colour-blind separation and contrast on both surfaces; the net worth line is in ink.

Months are named relative to the example's current month ("this month", "6 months
ago", "next month"), never by name or year: the images do not look dated months later,
while the examples behind them keep their fixed dates, so the generated files stay stable.
"""

from __future__ import annotations

import json
from typing import Any

WIDTH, HEIGHT = 720, 380
LEFT, RIGHT, TOP, BOTTOM = 64, 150, 96, 318
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

SCHEMES = {
    "light": {
        "surface": "#fcfcfb",
        "border": "#e6e5e0",
        "grid": "#e6e5e0",
        "primary": "#0b0b0b",
        "secondary": "#52514e",
        "end": "#2a78d6",
        "lowest": "#eb6834",
        "assets": "#2a78d6",
        "debts": "#eb6834",
    },
    "dark": {
        "surface": "#1a1a19",
        "border": "#383835",
        "grid": "#383835",
        "primary": "#ffffff",
        "secondary": "#c3c2b7",
        "end": "#3987e5",
        "lowest": "#d95926",
        "assets": "#3987e5",
        "debts": "#d95926",
    },
}


def _relative(offset: int) -> str:
    """Name a month by its distance from the current one, so the label never ages.

    Args:
        offset: Months after the current one; negative before it.

    Returns:
        E.g. "this month", "last month", "6 months ago", "next month" or "in 3 months".
    """
    if offset == 0:
        return "this month"
    if offset == -1:
        return "last month"
    if offset == 1:
        return "next month"
    return f"{-offset} months ago" if offset < 0 else f"in {offset} months"


def _money(value: float) -> str:
    """Write an amount the way the README reads it.

    Args:
        value: An amount in currency units.

    Returns:
        E.g. "12,395", or "−420" with a true minus sign.
    """
    text = f"{abs(value):,.0f}"
    return f"−{text}" if value < 0 else text


def _step(top: float) -> int:
    """Choose the spacing of the horizontal grid lines.

    Args:
        top: The largest value to show.

    Returns:
        A round step giving three to five lines.
    """
    for step in (1000, 2000, 2500, 5000, 10000, 20000, 25000, 50000):
        if top / step <= 4:
            return step
    return 100000


class _Scale:
    """Place months across and amounts up the plot area."""

    def __init__(self, months: list[dict[str, Any]]) -> None:
        """Fit the scale to a forecast's months.

        Args:
            months: The forecast's months.
        """
        highest = max(m["end"] for m in months)
        self.step = _step(highest)
        self.top = self.step * (int(highest // self.step) + 1)
        self.span = (WIDTH - LEFT - RIGHT - 48) / max(len(months) - 1, 1)

    def x(self, index: int) -> float:
        """Give the abscissa of a month.

        Args:
            index: The month's position, from 0.

        Returns:
            Its x coordinate.
        """
        return LEFT + 24 + index * self.span

    def y(self, value: float) -> float:
        """Give the ordinate of an amount.

        Args:
            value: An amount in currency units.

        Returns:
            Its y coordinate.
        """
        return BOTTOM - (value / self.top) * (BOTTOM - TOP)


def _frame(months: list[dict[str, Any]], colour: dict[str, str]) -> list[str]:
    """Open the SVG: accessible title and description, card, heading.

    Args:
        months: The forecast's months.
        colour: The scheme's colours.

    Returns:
        The opening elements.
    """
    summary = "; ".join(
        f"{_relative(index)}: month end {_money(m['end'])}, lowest day {_money(m['lowest'])}"
        for index, m in enumerate(months)
    )
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{FONT}" role="img" '
        'aria-labelledby="title desc">',
        '<title id="title">Projected balance of the demo plan, by month</title>',
        f'<desc id="desc">{summary}</desc>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" '
        f'fill="{colour["surface"]}" stroke="{colour["border"]}"/>',
        f'<text x="{LEFT - 40}" y="40" font-size="18" font-weight="600" '
        f'fill="{colour["primary"]}">Projected balance, month by month</text>',
        f'<text x="{LEFT - 40}" y="64" font-size="13" fill="{colour["secondary"]}">'
        "forecast_balance on the invented demo plan \u00b7 scheduled payments on their "
        "dates</text>",
    ]


def _axes(months: list[dict[str, Any]], scale: _Scale, colour: dict[str, str]) -> list[str]:
    """Draw the grid, its amounts, each month's distance from now and its span.

    Args:
        months: The forecast's months.
        scale: Where months and amounts go.
        colour: The scheme's colours.

    Returns:
        The elements, drawn under the marks.
    """
    parts = []
    for value in range(0, scale.top + 1, scale.step):
        parts.append(
            f'<line x1="{LEFT}" x2="{WIDTH - RIGHT + 24}" y1="{scale.y(value):.1f}" '
            f'y2="{scale.y(value):.1f}" stroke="{colour["grid"]}" stroke-width="1"/>'
        )
        label = "0" if value == 0 else f"{value // 1000}k"
        parts.append(
            f'<text x="{LEFT - 10}" y="{scale.y(value) + 4:.1f}" font-size="12" '
            f'text-anchor="end" fill="{colour["secondary"]}">{label}</text>'
        )
    for index, month in enumerate(months):
        parts.append(
            f'<text x="{scale.x(index):.1f}" y="{BOTTOM + 24}" font-size="12" '
            f'text-anchor="middle" fill="{colour["secondary"]}">'
            f"{_relative(index)}</text>"
        )
        # The span of the month, from its lowest day up to its end.
        parts.append(
            f'<line x1="{scale.x(index):.1f}" x2="{scale.x(index):.1f}" '
            f'y1="{scale.y(month["lowest"]):.1f}" y2="{scale.y(month["end"]):.1f}" '
            f'stroke="{colour["secondary"]}" stroke-width="1" stroke-dasharray="2 3"/>'
        )
    return parts


def _marks(months: list[dict[str, Any]], scale: _Scale, colour: dict[str, str]) -> list[str]:
    """Draw the month-end line and points, the lowest days, and their direct labels.

    Args:
        months: The forecast's months.
        scale: Where months and amounts go.
        colour: The scheme's colours.

    Returns:
        The elements.
    """
    points = " ".join(f"{scale.x(i):.1f},{scale.y(m['end']):.1f}" for i, m in enumerate(months))
    parts = [
        f'<polyline points="{points}" fill="none" stroke="{colour["end"]}" stroke-width="2" '
        'stroke-linejoin="round"/>'
    ]
    for index, month in enumerate(months):
        parts.append(
            f'<circle cx="{scale.x(index):.1f}" cy="{scale.y(month["end"]):.1f}" r="5" '
            f'fill="{colour["end"]}" stroke="{colour["surface"]}" stroke-width="2"/>'
        )
        parts.append(
            f'<rect x="{scale.x(index) - 5:.1f}" y="{scale.y(month["lowest"]) - 5:.1f}" '
            f'width="10" height="10" rx="2" fill="{colour["lowest"]}" '
            f'stroke="{colour["surface"]}" stroke-width="2"/>'
        )
    last = len(months) - 1
    for key, label in (("end", "Month end"), ("lowest", "Lowest day")):
        parts.append(
            f'<text x="{scale.x(last) + 14:.1f}" y="{scale.y(months[last][key]) + 4:.1f}" '
            f'font-size="13" fill="{colour["primary"]}">{label} '
            f"{_money(months[last][key])}</text>"
        )
    return parts


def _yearly(forecast: dict[str, Any], scale: _Scale, colour: dict[str, str]) -> list[str]:
    """Name each yearly scheduled payment beside the lowest day of its month.

    The label under its month already says when.

    Args:
        forecast: forecast_balance's answer.
        scale: Where months and amounts go.
        colour: The scheme's colours.

    Returns:
        The elements.
    """
    months = forecast["months"]
    # The example cuts long lists with a "… N more" line: only the listed items count.
    scheduled = [o for o in forecast["assumptions"]["scheduled"] if isinstance(o, dict)]
    parts = []
    for payment in (o for o in scheduled if o["frequency"] == "yearly"):
        index = next((i for i, m in enumerate(months) if m["month"] == payment["date"][:7]), None)
        if index is None:
            continue
        left, low = scale.x(index) + 12, scale.y(months[index]["lowest"])
        parts.append(
            f'<text x="{left:.1f}" y="{low + 4:.1f}" font-size="12" '
            f'fill="{colour["secondary"]}">'
            f"<tspan>{payment['payee'].title()} {_money(payment['amount'])}</tspan>"
            f'<tspan x="{left:.1f}" dy="15">yearly, scheduled in YNAB</tspan></text>'
        )
    return parts


def _outlook(months: list[dict[str, Any]]) -> str:
    """Say whether money runs out, as the tool's message does, without naming a month.

    Args:
        months: The forecast's months, the current one first.

    Returns:
        E.g. "The balance stays above zero for the 4 months shown."
    """
    short = next((i for i, m in enumerate(months) if m["lowest"] < 0), None)
    if short is None:
        return f"The balance stays above zero for the {len(months)} months shown."
    return f"The balance goes below zero {_relative(short)}."


def chart(forecast: dict[str, Any], scheme: str) -> str:
    """Draw the month-end and lowest balances of a forecast as an SVG.

    Args:
        forecast: forecast_balance's answer, as the documentation example holds it.
        scheme: "light" or "dark".

    Returns:
        The SVG document.
    """
    colour = SCHEMES[scheme]
    months = forecast["months"]
    scale = _Scale(months)
    parts = [
        *_frame(months, colour),
        *_axes(months, scale, colour),
        *_marks(months, scale, colour),
        *_yearly(forecast, scale, colour),
        f'<text x="{LEFT - 40}" y="{HEIGHT - 18}" font-size="12" '
        f'fill="{colour["secondary"]}">{_outlook(months)}</text>',
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def charts(snippet: str) -> dict[str, str]:
    """Draw the README chart in both colour schemes.

    Args:
        snippet: The forecast example, as JSON text.

    Returns:
        Each scheme's SVG, by scheme name.
    """
    forecast = json.loads(snippet)
    return {scheme: chart(forecast, scheme) for scheme in SCHEMES}


# The net worth chart: one column per month, assets above zero and debts below, the
# net worth as a line across them. Its own frame: months are many, labels go every third.
NW_TOP, NW_BOTTOM = 104, 318


def _signed(value: float) -> str:
    """Write an amount with its sign, for a change people read as a gain or a loss.

    Args:
        value: An amount in currency units.

    Returns:
        E.g. "+1,357" or "−15,387", with a true minus sign.
    """
    return _money(value) if value < 0 else f"+{_money(value)}"


class _NetScale:
    """Place months across and amounts, both signs, up the plot area."""

    def __init__(self, months: list[dict[str, Any]]) -> None:
        """Fit the scale to the months, zero included.

        Args:
            months: get_net_worth_trend's months.
        """
        highest = max(0.0, *(max(m["assets"], m["net_worth"]) for m in months))
        lowest = min(0.0, *(min(m["debts"], m["net_worth"]) for m in months))
        self.step = _step(max(highest, -lowest))
        self.top = self.step * (int(highest // self.step) + 1)
        self.bottom = -self.step * (int(-lowest // self.step) + 1)
        self.span = (WIDTH - LEFT - RIGHT - 24) / max(len(months) - 1, 1)

    def x(self, index: int) -> float:
        """Give the abscissa of a month's column.

        Args:
            index: The month's position, from 0.

        Returns:
            Its x coordinate.
        """
        return LEFT + 16 + index * self.span

    def y(self, value: float) -> float:
        """Give the ordinate of an amount.

        Args:
            value: An amount in currency units, negative below zero.

        Returns:
            Its y coordinate.
        """
        return NW_TOP + (self.top - value) / (self.top - self.bottom) * (NW_BOTTOM - NW_TOP)


def _bar(x: float, width: float, base: float, end: float, fill: str) -> str:
    """Draw a bar from the zero line, its far end rounded, its base square.

    Args:
        x: The bar's centre.
        width: Its width.
        base: The ordinate of zero.
        end: The ordinate of its value.
        fill: Its colour.

    Returns:
        The path element; nothing drawn for a zero value.
    """
    height = abs(end - base)
    if height < 0.5:
        return ""
    radius = min(4.0, height, width / 2)
    left, right = x - width / 2, x + width / 2
    way = -1 if end < base else 1  # -1 upwards: an asset; 1 downwards: a debt
    turn = end - way * radius
    sweep = 1 if way < 0 else 0
    return (
        f'<path d="M{left:.1f},{base:.1f} V{turn:.1f} '
        f"A{radius:.1f},{radius:.1f} 0 0 {sweep} {left + radius:.1f},{end:.1f} "
        f"H{right - radius:.1f} A{radius:.1f},{radius:.1f} 0 0 {sweep} {right:.1f},{turn:.1f} "
        f'V{base:.1f} Z" fill="{fill}"/>'
    )


def _net_frame(trend: dict[str, Any], colour: dict[str, str]) -> list[str]:
    """Open the net worth SVG: accessible title and description, card, heading.

    Args:
        trend: get_net_worth_trend's answer.
        colour: The scheme's colours.

    Returns:
        The opening elements.
    """
    months = trend["months"]
    last = len(months) - 1
    summary = "; ".join(
        f"{_relative(index - last)}: assets {_money(m['assets'])}, "
        f"debts {_money(m['debts'])}, net worth {_money(m['net_worth'])}"
        for index, m in enumerate(months)
    )
    heading = (
        f"Net worth: from {_signed(trend['first_net_worth'])} to "
        f"{_signed(trend['last_net_worth'])} in {len(months)} months"
    )
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{FONT}" role="img" '
        'aria-labelledby="title desc">',
        f'<title id="title">{heading}, on the demo plan</title>',
        f'<desc id="desc">{summary}</desc>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" '
        f'fill="{colour["surface"]}" stroke="{colour["border"]}"/>',
        f'<text x="{LEFT - 40}" y="40" font-size="18" font-weight="600" '
        f'fill="{colour["primary"]}">{heading}</text>',
        f'<text x="{LEFT - 40}" y="64" font-size="13" fill="{colour["secondary"]}">'
        "get_net_worth_trend on the invented demo plan \u00b7 assets above zero, debts "
        "below, at each month end</text>",
    ]


def _net_axes(months: list[dict[str, Any]], scale: _NetScale, colour: dict[str, str]) -> list[str]:
    """Draw the grid, its amounts, zero in ink, and a few months' distance from now.

    A label every six months back from the current one, and on the first month when it
    stands far enough from the next label.

    Args:
        months: get_net_worth_trend's months.
        scale: Where months and amounts go.
        colour: The scheme's colours.

    Returns:
        The elements, drawn under the marks.
    """
    parts = []
    for value in range(scale.bottom, scale.top + 1, scale.step):
        stroke = colour["secondary"] if value == 0 else colour["grid"]
        parts.append(
            f'<line x1="{LEFT}" x2="{WIDTH - RIGHT + 24}" y1="{scale.y(value):.1f}" '
            f'y2="{scale.y(value):.1f}" stroke="{stroke}" stroke-width="1"/>'
        )
        label = "0" if value == 0 else _money(value / 1000) + "k"
        parts.append(
            f'<text x="{LEFT - 10}" y="{scale.y(value) + 4:.1f}" font-size="12" '
            f'text-anchor="end" fill="{colour["secondary"]}">{label}</text>'
        )
    last = len(months) - 1
    ticks = list(range(last, -1, -6))
    if ticks[-1] >= 3:
        ticks.append(0)
    for index in reversed(ticks):
        parts.append(
            f'<text x="{scale.x(index):.1f}" y="{NW_BOTTOM + 24}" font-size="12" '
            f'text-anchor="middle" fill="{colour["secondary"]}">'
            f"{_relative(index - last)}</text>"
        )
    return parts


def _net_marks(months: list[dict[str, Any]], scale: _NetScale, colour: dict[str, str]) -> list[str]:
    """Draw the bars, the net worth line and its points, and the direct labels.

    Args:
        months: get_net_worth_trend's months.
        scale: Where months and amounts go.
        colour: The scheme's colours.

    Returns:
        The elements.
    """
    width = min(16.0, scale.span * 0.6)
    zero = scale.y(0)
    parts = []
    for index, month in enumerate(months):
        for key in ("assets", "debts"):
            parts.append(_bar(scale.x(index), width, zero, scale.y(month[key]), colour[key]))
    points = " ".join(
        f"{scale.x(i):.1f},{scale.y(m['net_worth']):.1f}" for i, m in enumerate(months)
    )
    parts.append(
        f'<polyline points="{points}" fill="none" stroke="{colour["primary"]}" '
        'stroke-width="2" stroke-linejoin="round"/>'
    )
    for index, month in enumerate(months):
        parts.append(
            f'<circle cx="{scale.x(index):.1f}" cy="{scale.y(month["net_worth"]):.1f}" r="4" '
            f'fill="{colour["primary"]}" stroke="{colour["surface"]}" stroke-width="2"/>'
        )
    last = len(months) - 1
    for key, label in (("assets", "Assets"), ("net_worth", "Net worth"), ("debts", "Debts")):
        swatch = colour["primary"] if key == "net_worth" else colour[key]
        y = scale.y(months[last][key])
        parts.append(
            f'<rect x="{scale.x(last) + 16:.1f}" y="{y - 5:.1f}" width="10" height="10" '
            f'rx="2" fill="{swatch}"/>'
        )
        parts.append(
            f'<text x="{scale.x(last) + 32:.1f}" y="{y + 4:.1f}" font-size="13" '
            f'fill="{colour["primary"]}">{label} {_money(months[last][key])}</text>'
        )
    return [part for part in parts if part]


def net_worth_chart(trend: dict[str, Any], scheme: str) -> str:
    """Draw assets, debts and net worth month by month as an SVG.

    Args:
        trend: get_net_worth_trend's answer, as the documentation example holds it.
        scheme: "light" or "dark".

    Returns:
        The SVG document.
    """
    colour = SCHEMES[scheme]
    months = trend["months"]
    scale = _NetScale(months)
    first, last = months[0], months[-1]
    footer = (
        f"Debts down from {_money(-first['debts'])} to {_money(-last['debts'])}; "
        f"net worth {_signed(trend['change'])} since {_relative(1 - len(months))}."
    )
    parts = [
        *_net_frame(trend, colour),
        *_net_axes(months, scale, colour),
        *_net_marks(months, scale, colour),
        f'<text x="{LEFT - 40}" y="{HEIGHT - 18}" font-size="12" '
        f'fill="{colour["secondary"]}">{footer}</text>',
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def net_worth_charts(snippet: str) -> dict[str, str]:
    """Draw the README's net worth chart in both colour schemes.

    Args:
        snippet: The net worth example, as JSON text.

    Returns:
        Each scheme's SVG, by scheme name.
    """
    trend = json.loads(snippet)
    return {scheme: net_worth_chart(trend, scheme) for scheme in SCHEMES}
