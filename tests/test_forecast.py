"""Tests for forecast.py — projecting balances from history and assumptions."""

from __future__ import annotations

from datetime import date
from typing import Any

from avenir_mcp import forecast

TODAY = date(2026, 9, 24)


def _tx(payee: str, amount: int, day: str, **extra: Any) -> dict[str, Any]:
    tx: dict[str, Any] = {
        "payee_name": payee,
        "amount": amount,
        "date": day,
        "deleted": False,
        "transfer_account_id": None,
        "account_id": "acc",
    }
    tx.update(extra)
    return tx


def _monthly(payee: str, amount: int, day: int, months: list[str]) -> list[dict[str, Any]]:
    return [_tx(payee, amount, f"{m}-{day:02d}") for m in months]


# ---------------------------------------------------------------------------
# recurring
# ---------------------------------------------------------------------------


def test_stable_monthly_charge_is_recurring() -> None:
    """A payee charged about the same amount in 3 of the last 4 full months recurs."""
    txs = _monthly("CAR LEASE", -364080, 25, ["2026-05", "2026-06", "2026-08"])
    assert forecast.recurring(txs, TODAY) == [
        forecast.Recurring(payee="CAR LEASE", amount=-364.08, day=25, months_seen=3)
    ]


def test_recurring_payee_is_shown_without_invisible_characters() -> None:
    """A payee name in the assumptions is safe to show."""
    txs = _monthly("CAR\u202e LEASE", -364080, 25, ["2026-05", "2026-06", "2026-08"])
    assert forecast.recurring(txs, TODAY)[0].payee == "CAR LEASE"


def test_irregular_or_rare_payees_are_not_recurring() -> None:
    """Seen twice, or with amounts varying more than 20 %, is not a subscription."""
    txs = _monthly("RARE", -10000, 3, ["2026-07", "2026-08"]) + [
        _tx("RESTAURANT", -20000, "2026-05-02"),
        _tx("RESTAURANT", -60000, "2026-06-02"),
        _tx("RESTAURANT", -30000, "2026-07-02"),
    ]
    assert not forecast.recurring(txs, TODAY)


def test_current_month_and_old_months_are_ignored() -> None:
    """Only the last 4 full months count: the current one is incomplete."""
    txs = _monthly("OLD", -5000, 5, ["2026-01", "2026-02", "2026-03"]) + _monthly(
        "NEW", -5000, 5, ["2026-08", "2026-09"]
    )
    assert not forecast.recurring(txs, TODAY)


def test_transfers_and_deleted_transactions_are_ignored() -> None:
    """Moving money between accounts is not a charge."""
    txs = [
        _tx("SAVINGS", -5000, f"{m}-05", transfer_account_id="acc-2")
        for m in ("2026-05", "2026-06", "2026-07")
    ]
    txs += [_tx("GONE", -5000, f"{m}-05", deleted=True) for m in ("2026-05", "2026-06", "2026-07")]
    assert not forecast.recurring(txs, TODAY)


# ---------------------------------------------------------------------------
# variable_average
# ---------------------------------------------------------------------------


def test_variable_spending_is_the_monthly_average_of_the_rest() -> None:
    """Outflows that are not recurring, averaged over the last 3 full months."""
    txs = _monthly("CAR LEASE", -100000, 25, ["2026-06", "2026-07", "2026-08"]) + [
        _tx("RESTAURANT", -30000, "2026-06-10"),
        _tx("TRAIN", -60000, "2026-07-10"),
        _tx("RESTAURANT", -30000, "2026-08-10"),
        _tx("CLIENT", 500000, "2026-08-10"),
    ]
    rec = forecast.recurring(txs, TODAY)
    assert forecast.variable_average(txs, TODAY, rec) == -40.0


# ---------------------------------------------------------------------------
# project
# ---------------------------------------------------------------------------


def test_projection_walks_month_by_month_and_flags_the_first_shortfall() -> None:
    """Each month starts where the previous ended; the first negative month is named."""
    result = forecast.project(
        start_balance=1000.0,
        today=TODAY,
        until="2026-12",
        recurring=[forecast.Recurring(payee="CAR LEASE", amount=-400.0, day=25, months_seen=4)],
        variable_monthly=-300.0,
        monthly_income=0.0,
        one_offs=[forecast.OneOff(date=date(2026, 11, 15), amount=200.0, label="refund")],
    )
    months = result.months
    assert [m.month for m in months] == ["2026-09", "2026-10", "2026-11", "2026-12"]
    # September: only what is still to come — the lease on the 25th and, since
    # nothing was spent yet this month, the month's variable spending.
    assert months[0].start == 1000.0
    assert months[0].end == 1000.0 - 400.0 - 300.0
    assert months[1].start == months[0].end
    assert months[2].inflows == 200.0
    assert result.first_shortfall == "2026-10"
    assert months[1].lowest < 0


def test_projection_counts_monthly_income() -> None:
    """Expected income is added every full month."""
    result = forecast.project(
        start_balance=0.0,
        today=TODAY,
        until="2026-10",
        recurring=[],
        variable_monthly=0.0,
        monthly_income=3000.0,
        one_offs=[],
    )
    assert result.months[0].end == 3000.0  # not received yet this month
    assert result.months[1].inflows == 3000.0
    assert result.months[1].end == 6000.0
    assert result.first_shortfall is None


def test_one_offs_outside_the_period_are_ignored() -> None:
    """A one-off before today or after the horizon does not count."""
    result = forecast.project(
        start_balance=100.0,
        today=TODAY,
        until="2026-10",
        recurring=[],
        variable_monthly=0.0,
        monthly_income=0.0,
        one_offs=[
            forecast.OneOff(date=date(2026, 9, 1), amount=-50.0, label="past"),
            forecast.OneOff(date=date(2027, 1, 1), amount=-50.0, label="later"),
        ],
    )
    assert result.months[-1].end == 100.0


def test_january_looks_back_into_the_previous_year() -> None:
    """In January the last full months belong to the year before."""
    txs = _monthly("RENT", -50000, 1, ["2025-10", "2025-11", "2025-12"])
    assert forecast.recurring(txs, date(2026, 1, 10))[0].payee == "RENT"


def test_transactions_without_payee_are_not_recurring() -> None:
    """A blank payee names nothing that could recur."""
    txs = _monthly("", -5000, 5, ["2026-05", "2026-06", "2026-07"])
    assert not forecast.recurring(txs, TODAY)


def test_income_average_is_the_monthly_average_of_non_recurring_inflows() -> None:
    """Money in over the last 3 full months, recurring income excluded."""
    txs = _monthly("RENT PAID TO ME", 500000, 1, ["2026-06", "2026-07", "2026-08"]) + [
        _tx("CLIENT A", 3000000, "2026-06-30"),
        _tx("CLIENT B", 6000000, "2026-08-30"),
        _tx("SHOP", -100000, "2026-08-02"),
    ]
    rec = forecast.recurring(txs, TODAY)
    assert forecast.income_average(txs, TODAY, rec) == 3000.0


def test_projection_amounts_are_whole_cents() -> None:
    """Spreading spending over days never leaves fractions of a cent."""
    result = forecast.project(
        start_balance=0.0,
        today=date(2026, 9, 24),
        until="2026-10",
        recurring=[],
        variable_monthly=-100.0,
        monthly_income=0.0,
        one_offs=[],
    )
    for month in result.months:
        for key in ("inflows", "outflows", "end", "lowest"):
            value = getattr(month, key)
            assert value == round(value, 2)
    assert result.months[0].end == -100.0
    assert result.months[1].end == -200.0


def test_current_month_counts_only_what_is_left_to_spend_and_receive() -> None:
    """What already happened this month is deducted from the monthly averages."""

    def september_end(spent: float, received: float) -> float:
        return (
            forecast.project(
                start_balance=0.0,
                today=TODAY,
                until="2026-09",
                recurring=[],
                variable_monthly=-300.0,
                monthly_income=1000.0,
                one_offs=[],
                spent_this_month=spent,
                received_this_month=received,
            )
            .months[0]
            .end
        )

    assert september_end(-250.0, 400.0) == -50.0 + 600.0
    assert september_end(-400.0, 1500.0) == 0.0


def test_spending_is_spread_so_income_can_cover_it() -> None:
    """A month whose income covers its spending never dips below its start."""
    result = forecast.project(
        start_balance=0.0,
        today=TODAY,
        until="2026-10",
        recurring=[],
        variable_monthly=-3000.0,
        monthly_income=3000.0,
        one_offs=[],
    )
    assert result.months[1].lowest > -200.0


def test_last_day_of_the_month_has_nothing_left_to_spread() -> None:
    """On the last day of a month, nothing more is projected for it."""
    result = forecast.project(
        start_balance=10.0,
        today=date(2026, 9, 30),
        until="2026-09",
        recurring=[],
        variable_monthly=-300.0,
        monthly_income=0.0,
        one_offs=[],
    )
    assert result.months[0].end == 10.0


def test_month_to_date_sums_this_month_without_recurring_amounts() -> None:
    """What was spent and received since the 1st, recurring amounts excluded."""
    txs = _monthly("CAR LEASE", -400000, 5, ["2026-06", "2026-07", "2026-08", "2026-09"]) + [
        _tx("TAX", -1638000, "2026-09-24"),
        _tx("CLIENT", 500000, "2026-09-10"),
        _tx("LAST MONTH", -1000, "2026-08-31"),
    ]
    rec = forecast.recurring(txs, TODAY)
    assert forecast.month_to_date(txs, TODAY, rec) == (-1638.0, 500.0)


# ---------------------------------------------------------------------------
# Cases found by mutation testing
# ---------------------------------------------------------------------------


def test_several_charges_of_a_payee_in_a_month_add_up() -> None:
    """Two instalments to the same payee in a month count as one monthly charge, summed."""
    txs = [
        _tx("GYM", amount, f"{month}-{day:02d}")
        for month in ("2026-05", "2026-06", "2026-07")
        for amount, day in ((-20000, 3), (-10000, 18))
    ]
    assert forecast.recurring(txs, TODAY)[0].amount == -30.0


def test_month_to_date_adds_every_payment() -> None:
    """Spending and income since the 1st are sums, not the last payment seen."""
    txs = [
        _tx("SHOP", -10000, "2026-09-02"),
        _tx("SHOP", -25000, "2026-09-10"),
        _tx("CLIENT", 40000, "2026-09-05"),
        _tx("CLIENT", 60000, "2026-09-12"),
    ]
    assert forecast.month_to_date(txs, TODAY, []) == (-35.0, 100.0)


def test_the_projection_crosses_the_new_year() -> None:
    """From November to February, the months follow each other across December."""
    result = forecast.project(
        start_balance=0.0,
        today=date(2026, 11, 20),
        until="2027-02",
        recurring=[],
        variable_monthly=0.0,
        monthly_income=0.0,
        one_offs=[],
    )
    assert [m.month for m in result.months] == ["2026-11", "2026-12", "2027-01", "2027-02"]


def test_charges_and_one_offs_on_the_same_day_add_up() -> None:
    """Two amounts falling on one day both count."""
    result = forecast.project(
        start_balance=0.0,
        today=TODAY,
        until="2026-10",
        recurring=[
            forecast.Recurring(payee="RENT", amount=-500.0, day=5, months_seen=4),
            forecast.Recurring(payee="PHONE", amount=-20.0, day=5, months_seen=4),
        ],
        variable_monthly=0.0,
        monthly_income=0.0,
        one_offs=[
            forecast.OneOff(date=date(2026, 10, 5), amount=-100.0, label="tax"),
            forecast.OneOff(date=date(2026, 10, 5), amount=-50.0, label="fine"),
        ],
    )
    assert result.months[1].outflows == -670.0


def test_a_one_off_dated_today_has_already_happened() -> None:
    """Only amounts after today are projected: one dated today is in today's balance."""
    result = forecast.project(
        start_balance=100.0,
        today=TODAY,
        until="2026-09",
        recurring=[],
        variable_monthly=0.0,
        monthly_income=0.0,
        one_offs=[forecast.OneOff(date=TODAY, amount=-50.0, label="paid today")],
    )
    assert result.months[0].end == 100.0


def test_next_months_are_whole_whatever_was_spent_this_month() -> None:
    """A month after this one starts on the 1st, with full averages and every charge."""
    result = forecast.project(
        start_balance=0.0,
        today=TODAY,
        until="2026-10",
        recurring=[forecast.Recurring(payee="RENT", amount=-500.0, day=2, months_seen=4)],
        variable_monthly=-300.0,
        monthly_income=1000.0,
        one_offs=[],
        spent_this_month=-250.0,
        received_this_month=400.0,
    )
    october = result.months[1]
    assert (october.inflows, october.outflows) == (1000.0, -800.0)


def test_a_charge_on_the_first_of_a_coming_month_counts() -> None:
    """A month after this one is projected from its first day."""
    result = forecast.project(
        start_balance=0.0,
        today=TODAY,
        until="2026-10",
        recurring=[forecast.Recurring(payee="RENT", amount=-500.0, day=1, months_seen=4)],
        variable_monthly=0.0,
        monthly_income=0.0,
        one_offs=[],
    )
    assert result.months[1].outflows == -500.0


def test_in_january_the_four_months_before_reach_back_to_september() -> None:
    """September, November and December make three of the last four full months."""
    txs = _monthly("RENT", -50000, 1, ["2025-09", "2025-11", "2025-12"])
    assert forecast.recurring(txs, date(2026, 1, 10))[0].months_seen == 3


def test_scheduled_payees_are_left_out_of_the_averages() -> None:
    """A payee with a schedule is projected by it, so it leaves the averages and month to date."""
    txs = [
        _tx("INSURANCE", -300000, "2026-08-10"),
        _tx("SHOP", -30000, "2026-08-12"),
        _tx("INSURANCE", -120000, "2026-09-02"),
        _tx("CLIENT", 90000, "2026-07-10"),
    ]
    scheduled = frozenset({("INSURANCE", True), ("CLIENT", False)})
    assert forecast.variable_average(txs, TODAY, [], also=scheduled) == -10.0
    assert forecast.income_average(txs, TODAY, [], also=scheduled) == 0.0
    assert forecast.month_to_date(txs, TODAY, [], also=scheduled) == (0.0, 0.0)
