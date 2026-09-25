"""The evaluation's own checks must be right, or its scores mean nothing."""

from __future__ import annotations

import httpx
import pytest

from evals import fake_ynab, tasks


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("€3,512.66", [3512.66]),
        ("3 512,66 €", [3512.66]),
        ("-22.5", [-22.5]),
        ("89.10 € in August 2026", [89.10, 2026.0]),
        ("6 transactions", [6.0]),
        ("1 234,5", [1234.5]),
    ],
)
def test_amounts_are_read_as_people_write_them(text: str, expected: list[float]) -> None:
    """Thousands separators and decimal commas are both understood."""
    assert tasks.parse_amounts(text) == pytest.approx(expected)


def test_expected_answers_come_from_the_demo_data() -> None:
    """The figures the agent must find, computed from the invented budget."""
    assert tasks.RESTAURANTS_AUGUST == pytest.approx(89.10)
    assert tasks.RESTAURANTS_SEPTEMBER_OVER == pytest.approx(-22.5)
    assert tasks.CHECKING == pytest.approx(3512.66)


def test_demo_server_answers_like_ynab() -> None:
    """Budgets by id or by "last-used"; unknown paths get YNAB's 404."""
    server = fake_ynab.serve()
    base = f"http://127.0.0.1:{server.server_port}/v1"
    try:
        for budget in ("demo-budget", "last-used"):
            accounts = httpx.get(f"{base}/budgets/{budget}/accounts").json()["data"]["accounts"]
            assert {a["name"] for a in accounts} == {"Checking", "Savings"}
        assert httpx.get(f"{base}/budgets/other/accounts").status_code == 404
    finally:
        server.shutdown()
