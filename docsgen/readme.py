"""The forecast chart at the top of the README, drawn from the documented example.

The example is `forecast_balance` on the demo plan (`docs/src/snippets/forecast.json`),
so the chart shows what the tool answers today, and the test of generated files
fails when it no longer does. One SVG per colour scheme: GitHub picks it with
`<picture>`. Colours are the reference palette's first two categorical slots,
checked for colour-blind separation and contrast on both surfaces.
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
    },
    "dark": {
        "surface": "#1a1a19",
        "border": "#383835",
        "grid": "#383835",
        "primary": "#ffffff",
        "secondary": "#c3c2b7",
        "end": "#3987e5",
        "lowest": "#d95926",
    },
}

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


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
        f"{m['month']}: month end {_money(m['end'])}, lowest day {_money(m['lowest'])}"
        for m in months
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
    """Draw the grid, its amounts, the month names and each month's span.

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
            f"{MONTHS[int(month['month'][5:7]) - 1]}</text>"
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
        day = f"{int(payment['date'][8:])} {MONTHS[int(payment['date'][5:7]) - 1]}"
        parts.append(
            f'<text x="{left:.1f}" y="{low + 4:.1f}" font-size="12" '
            f'fill="{colour["secondary"]}">'
            f"<tspan>{payment['payee'].title()} {_money(payment['amount'])}, {day}</tspan>"
            f'<tspan x="{left:.1f}" dy="15">yearly, scheduled in YNAB</tspan></text>'
        )
    return parts


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
        f'fill="{colour["secondary"]}">{forecast["message"].split(".")[0]}.</text>',
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
