"""Properties that hold for any input, checked on thousands of generated cases (Hypothesis)."""

from __future__ import annotations

import random
import unicodedata
from datetime import date, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from avenir_mcp import client, forecast, text, triage, writes
from avenir_mcp.amounts import MAX_AMOUNT

# Every amount a tool accepts, in currency units, and the milliunits YNAB stores.
amounts = st.floats(min_value=-MAX_AMOUNT, max_value=MAX_AMOUNT, allow_nan=False)
milliunits = st.integers(min_value=-MAX_AMOUNT * 1000, max_value=MAX_AMOUNT * 1000)


# ---------------------------------------------------------------------------
# Amounts
# ---------------------------------------------------------------------------


@given(milliunits)
def test_milliunits_survive_the_way_through_currency_units(value: int) -> None:
    """What YNAB stores comes back unchanged after being shown in currency units."""
    assert client.amount_to_milliunit(client.milliunit_to_amount(value)) == value


@given(amounts)
def test_an_amount_is_never_off_by_more_than_half_a_milliunit(amount: float) -> None:
    """Converting to milliunits rounds, it never drifts."""
    assert abs(client.amount_to_milliunit(amount) - amount * 1000) <= 0.5 + abs(amount) * 1e-12


@given(st.sampled_from([float("nan"), float("inf"), float("-inf")]))
def test_a_non_finite_amount_is_refused(amount: float) -> None:
    """NaN and infinities never reach YNAB."""
    with pytest.raises(ValueError, match="finite"):
        client.amount_to_milliunit(amount)


# ---------------------------------------------------------------------------
# Forecast: spreading money over days
# ---------------------------------------------------------------------------


@given(milliunits, st.integers(min_value=1, max_value=31), st.integers(min_value=0, max_value=31))
def test_spreading_keeps_every_cent_and_stays_even(total: int, first: int, span: int) -> None:
    """Spread over days, an amount keeps its whole cents; shares differ by one cent at most."""
    last = min(first + span, 31)
    shares = forecast._spread(total, first, last)  # pylint: disable=protected-access
    if not total:
        assert not shares
        return
    assert sorted(shares) == list(range(first, last + 1))
    assert sum(shares.values()) == total // 10 * 10
    assert all(share % 10 == 0 for share in shares.values())
    assert max(shares.values()) - min(shares.values()) <= 10


def _next_month(label: str) -> str:
    """The month after a YYYY-MM label."""
    year, number = int(label[:4]), int(label[5:])
    return f"{year + 1}-01" if number == 12 else f"{year}-{number + 1:02d}"


@settings(max_examples=200)
@given(
    start=st.integers(min_value=-10_000_000, max_value=10_000_000),
    variable=st.integers(min_value=-5_000_000, max_value=0),
    income=st.integers(min_value=0, max_value=5_000_000),
    today=st.dates(min_value=date(2026, 1, 1), max_value=date(2027, 12, 31)),
    months=st.integers(min_value=0, max_value=6),
)
def test_projected_months_follow_on_and_add_up(  # pylint: disable=too-many-arguments
    start: int, variable: int, income: int, today: date, months: int
) -> None:
    """Each month starts where the last ended, and ends at start plus inflows plus outflows."""
    until = today.replace(day=1) + timedelta(days=31 * months)
    projection = forecast.project(
        start_balance=start / 100,
        today=today,
        until=f"{until:%Y-%m}",
        recurring=[],
        variable_monthly=variable / 100,
        monthly_income=income / 100,
        one_offs=[],
    )
    assert projection.months[0].start == start / 100
    labels = [month.month for month in projection.months]
    assert labels[0] == f"{today:%Y-%m}" and labels[-1] == f"{until:%Y-%m}"
    assert all(_next_month(before) == after for before, after in zip(labels, labels[1:]))
    for month in projection.months:
        assert round(month.start + month.inflows + month.outflows, 2) == month.end
        assert month.lowest <= min(month.start, month.end)
    for before, after in zip(projection.months, projection.months[1:]):
        assert after.start == before.end
    shortfalls = [m.month for m in projection.months if m.lowest < 0]
    assert projection.first_shortfall == (shortfalls[0] if shortfalls else None)


# ---------------------------------------------------------------------------
# Pagination cursors
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=10**12))
def test_a_cursor_gives_back_its_offset(offset: int) -> None:
    """A cursor issued for an offset leads back to that offset."""
    cursor = triage._encode_cursor(offset)  # pylint: disable=protected-access
    assert triage._decode_cursor(cursor) == offset  # pylint: disable=protected-access


@given(st.text())
def test_any_other_cursor_is_refused_with_a_way_forward(cursor: str) -> None:
    """Whatever an agent passes as a cursor, the answer is an offset or a clear refusal."""
    try:
        offset = triage._decode_cursor(cursor)  # pylint: disable=protected-access
    except ValueError as error:
        assert "next_cursor" in str(error)
    else:
        assert offset >= 0


# ---------------------------------------------------------------------------
# Bank text
# ---------------------------------------------------------------------------


@given(st.one_of(st.none(), st.text()))
def test_bank_text_is_one_short_line_of_visible_characters(raw: str | None) -> None:
    """No line break, control or invisible character survives, and the length is bounded."""
    shown = text.untrusted(raw)
    assert len(shown) <= text.MAX_TEXT
    assert shown == shown.strip()
    assert "  " not in shown
    assert not any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in shown)


@given(st.text())
def test_bank_text_made_safe_stays_the_same_when_made_safe_again(raw: str) -> None:
    """Cleaning is stable: showing a cleaned text again changes nothing."""
    once = text.untrusted(raw)
    assert text.untrusted(once) == once


# ---------------------------------------------------------------------------
# Confirmation codes
# ---------------------------------------------------------------------------


@given(
    st.lists(
        st.dictionaries(st.sampled_from(["id", "to", "amount"]), st.integers(), min_size=1),
        max_size=8,
    ),
    st.randoms(use_true_random=False),
)
def test_a_preview_hashes_the_same_in_any_order(
    changes: list[dict[str, int]], rng: random.Random
) -> None:
    """A code confirms the same changes whatever their order in the list."""
    shuffled = list(changes)
    rng.shuffle(shuffled)
    assert writes.fingerprint("b1", changes) == writes.fingerprint("b1", shuffled)


@given(st.dictionaries(st.text(max_size=5), st.integers(), min_size=1))
def test_a_preview_of_other_changes_hashes_differently(subject: dict[str, int]) -> None:
    """Changing one value of what is confirmed changes the fingerprint."""
    key = next(iter(subject))
    other = {**subject, key: subject[key] + 1}
    assert writes.fingerprint("b1", subject) != writes.fingerprint("b1", other)
    assert writes.fingerprint("b1", subject) != writes.fingerprint("b2", subject)
