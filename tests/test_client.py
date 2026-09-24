"""Tests for client.py — YNAB API wrapper."""

# pylint: disable=redefined-outer-name

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from avenir_mcp import client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(payload: Any, status_code: int = 200) -> MagicMock:
    """Build a mock httpx response that returns *payload* as JSON."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _async_client_returning(payload: Any) -> MagicMock:
    """Return a context-manager mock whose .get() / .patch() yields *payload*."""
    mock_resp = _mock_response(payload)
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    mock_http.patch = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


# ---------------------------------------------------------------------------
# milliunit_to_amount
# ---------------------------------------------------------------------------


def test_milliunit_to_amount_positive() -> None:
    """500 000 milliunits should equal 500.0."""
    assert client.milliunit_to_amount(500_000) == 500.0


def test_milliunit_to_amount_negative() -> None:
    """-75 000 milliunits should equal -75.0."""
    assert client.milliunit_to_amount(-75_000) == -75.0


def test_milliunit_to_amount_zero() -> None:
    """0 milliunits should equal 0.0."""
    assert client.milliunit_to_amount(0) == 0.0


# ---------------------------------------------------------------------------
# _api_key
# ---------------------------------------------------------------------------


def test_api_key_raises_when_missing() -> None:
    """Should raise RuntimeError if YNAB_API_KEY is not set."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="YNAB_API_KEY"):
            client._api_key()  # pylint: disable=protected-access


def test_api_key_returns_env_value() -> None:
    """Should return the value of YNAB_API_KEY."""
    with patch.dict("os.environ", {"YNAB_API_KEY": "tok_abc"}):
        assert client._api_key() == "tok_abc"  # pylint: disable=protected-access


# ---------------------------------------------------------------------------
# get_budgets
# ---------------------------------------------------------------------------


def test_get_budgets_returns_list() -> None:
    """get_budgets should return the budgets list from the API payload."""
    payload = {"data": {"budgets": [{"id": "b1", "name": "Business"}]}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_budgets())
    assert result == [{"id": "b1", "name": "Business"}]


# ---------------------------------------------------------------------------
# get_categories
# ---------------------------------------------------------------------------


def test_get_categories_flattens_groups() -> None:
    """get_categories should return a flat list of non-hidden categories."""
    payload = {
        "data": {
            "category_groups": [
                {
                    "id": "g1",
                    "categories": [
                        {"id": "c1", "name": "Rent", "hidden": False},
                        {"id": "c2", "name": "Old", "hidden": True},
                    ],
                },
                {
                    "id": "g2",
                    "categories": [
                        {"id": "c3", "name": "AWS", "hidden": False},
                    ],
                },
            ]
        }
    }
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_categories("last-used"))
    assert len(result) == 2
    assert result[0]["id"] == "c1"
    assert result[1]["id"] == "c3"


# ---------------------------------------------------------------------------
# get_transactions — filters and delta sync
# ---------------------------------------------------------------------------


def test_get_transactions_uncategorized_passes_type_param() -> None:
    """uncategorized_only=True should add type=uncategorized to query params."""
    payload = {"data": {"transactions": [], "server_knowledge": 5}}
    mock_resp = _mock_response(payload)
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            asyncio.run(client.get_transactions("b1", uncategorized_only=True))

    call_kwargs = mock_http.get.call_args
    assert call_kwargs.kwargs["params"].get("type") == "uncategorized"


def test_get_transactions_delta_sync_uses_cached_knowledge() -> None:
    """Second call for same budget should pass last_knowledge_of_server."""
    payload = {"data": {"transactions": [{"id": "t1"}], "server_knowledge": 42}}
    ctx = _async_client_returning(payload)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            # First call populates cache
            asyncio.run(client.get_transactions("b1"))

    # Second call should use server_knowledge=42
    mock_resp2 = _mock_response({"data": {"transactions": [], "server_knowledge": 43}})
    mock_http2 = AsyncMock()
    mock_http2.get = AsyncMock(return_value=mock_resp2)
    ctx2 = MagicMock()
    ctx2.__aenter__ = AsyncMock(return_value=mock_http2)
    ctx2.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=ctx2):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            asyncio.run(client.get_transactions("b1"))

    call_kwargs = mock_http2.get.call_args
    assert call_kwargs.kwargs["params"].get("last_knowledge_of_server") == 42


def _get_transactions_twice(
    first: list[dict[str, Any]], delta: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Load a budget's transactions, then reload it when YNAB returns only `delta`."""
    with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
        payload = {"data": {"transactions": first, "server_knowledge": 1}}
        with patch("httpx.AsyncClient", return_value=_async_client_returning(payload)):
            asyncio.run(client.get_transactions("b1"))
        payload = {"data": {"transactions": delta, "server_knowledge": 2}}
        with patch("httpx.AsyncClient", return_value=_async_client_returning(payload)):
            return asyncio.run(client.get_transactions("b1"))


def test_get_transactions_delta_sync_returns_full_list_when_nothing_changed() -> None:
    """An empty delta means nothing changed, not that the budget is empty."""
    first = [{"id": "t1", "deleted": False}, {"id": "t2", "deleted": False}]
    assert _get_transactions_twice(first, []) == first


def test_get_transactions_delta_sync_merges_changes() -> None:
    """A delta updates changed transactions, adds new ones and drops deleted ones."""
    first = [
        {"id": "t1", "memo": "old", "deleted": False},
        {"id": "t2", "deleted": False},
    ]
    delta = [
        {"id": "t1", "memo": "new", "deleted": False},
        {"id": "t2", "deleted": True},
        {"id": "t3", "deleted": False},
    ]
    assert _get_transactions_twice(first, delta) == [
        {"id": "t1", "memo": "new", "deleted": False},
        {"id": "t3", "deleted": False},
    ]


def test_get_transactions_by_category_uses_category_endpoint() -> None:
    """Passing category_id should hit the category-specific endpoint."""
    payload = {"data": {"transactions": [{"id": "t9"}]}}
    mock_resp = _mock_response(payload)
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_transactions("b1", category_id="cat-42"))

    assert result == [{"id": "t9"}]
    url_called = mock_http.get.call_args.args[0]
    assert "categories/cat-42/transactions" in url_called


# ---------------------------------------------------------------------------
# patch_transaction
# ---------------------------------------------------------------------------


def test_get_month_returns_month_dict() -> None:
    """get_month should return the 'month' key from the API response."""
    payload = {
        "data": {
            "month": {
                "month": "2026-04-01",
                "budgeted": 5_000_000,
                "activity": -3_200_000,
                "balance": 1_800_000,
                "income": 8_000_000,
                "overspend": 0,
                "categories": [],
            }
        }
    }
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_month("b1", "2026-04-01"))
    assert result["month"] == "2026-04-01"
    assert result["budgeted"] == 5_000_000


def test_get_month_categories_flattens_nested_groups() -> None:
    """get_month_categories should flatten categories from nested group dicts."""
    month_payload = {
        "data": {
            "month": {
                "month": "2026-04-01",
                "budgeted": 0,
                "activity": 0,
                "balance": 0,
                "income": 0,
                "overspend": 0,
                "categories": [
                    {
                        "id": "g1",
                        "categories": [
                            {"id": "c1", "name": "Rent", "budgeted": 500_000},
                            {"id": "c2", "name": "AWS", "budgeted": 200_000},
                        ],
                    }
                ],
            }
        }
    }
    ctx = _async_client_returning(month_payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_month_categories("b1", "2026-04-01"))
    assert len(result) == 2
    assert result[0]["id"] == "c1"


def test_get_month_categories_flat_list() -> None:
    """get_month_categories handles a flat category list (no nested groups)."""
    month_payload = {
        "data": {
            "month": {
                "month": "2026-04-01",
                "budgeted": 0,
                "activity": 0,
                "balance": 0,
                "income": 0,
                "overspend": 0,
                "categories": [
                    {"id": "c1", "name": "Rent", "budgeted": 500_000},
                ],
            }
        }
    }
    ctx = _async_client_returning(month_payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_month_categories("b1", "2026-04-01"))
    assert len(result) == 1
    assert result[0]["id"] == "c1"


def test_get_transactions_with_since_date_skips_delta_sync() -> None:
    """Passing since_date should add the date param and NOT use delta sync."""
    payload = {"data": {"transactions": [{"id": "t5"}], "server_knowledge": 10}}
    mock_resp = _mock_response(payload)
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_transactions("b1", since_date="2026-01-01"))

    assert result == [{"id": "t5"}]
    call_kwargs = mock_http.get.call_args
    assert call_kwargs.kwargs["params"].get("since_date") == "2026-01-01"
    assert "last_knowledge_of_server" not in call_kwargs.kwargs["params"]


def test_get_months_returns_list() -> None:
    """get_months should return the months list from the API payload."""
    payload = {"data": {"months": [{"month": "2026-03-01"}, {"month": "2026-04-01"}]}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_months("b1"))
    assert result == [{"month": "2026-03-01"}, {"month": "2026-04-01"}]


def test_get_transaction_returns_transaction_dict() -> None:
    """get_transaction should return the transaction dict from the API payload."""
    payload = {"data": {"transaction": {"id": "t42", "payee_name": "AWS"}}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_transaction("b1", "t42"))
    assert result == {"id": "t42", "payee_name": "AWS"}


def test_patch_transaction_sends_correct_body() -> None:
    """classify_transaction should PUT {transaction: {category_id: ...}}."""
    payload = {"data": {"transaction": {"id": "t1", "category_id": "c99"}}}
    mock_resp = _mock_response(payload)
    mock_http = AsyncMock()
    mock_http.patch = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.patch_transaction("b1", "t1", "c99"))

    assert result["category_id"] == "c99"
    sent_json = mock_http.patch.call_args.kwargs["json"]
    assert sent_json == {"transaction": {"category_id": "c99"}}


def test_patch_transaction_adds_flag_color_when_given() -> None:
    """An optional flag_color is sent alongside the category."""
    payload = {"data": {"transaction": {"id": "t1", "category_id": "c99", "flag_color": "purple"}}}
    mock_http = AsyncMock()
    mock_http.patch = AsyncMock(return_value=_mock_response(payload))
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            asyncio.run(client.patch_transaction("b1", "t1", "c99", flag_color="purple"))

    sent_json = mock_http.patch.call_args.kwargs["json"]
    assert sent_json == {"transaction": {"category_id": "c99", "flag_color": "purple"}}


# ---------------------------------------------------------------------------
# get_category_groups / create_category
# ---------------------------------------------------------------------------


def test_get_category_groups_skips_hidden_deleted_and_internal() -> None:
    """get_category_groups returns only user-visible groups, without their categories."""
    payload = {
        "data": {
            "category_groups": [
                {
                    "id": "g0",
                    "name": "Internal Master Category",
                    "hidden": False,
                    "deleted": False,
                    "categories": [],
                },
                {
                    "id": "g1",
                    "name": "Software",
                    "hidden": False,
                    "deleted": False,
                    "categories": [{"id": "c1"}],
                },
                {
                    "id": "g2",
                    "name": "Archived",
                    "hidden": True,
                    "deleted": False,
                    "categories": [],
                },
                {
                    "id": "g4",
                    "name": "Credit Card Payments",
                    "hidden": False,
                    "deleted": False,
                    "categories": [],
                },
                {
                    "id": "g5",
                    "name": "Hidden Categories",
                    "hidden": False,
                    "deleted": False,
                    "categories": [],
                },
                {
                    "id": "g3",
                    "name": "Deleted",
                    "hidden": False,
                    "deleted": True,
                    "categories": [],
                },
            ]
        }
    }
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_category_groups("b1"))
    assert result == [{"id": "g1", "name": "Software"}]


def test_create_category_posts_name_and_group() -> None:
    """create_category should POST {category: {name, category_group_id}}."""
    payload = {"data": {"category": {"id": "c42", "name": "Miscellaneous"}, "server_knowledge": 7}}
    mock_resp = _mock_response(payload)
    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.create_category("b1", "g1", "Miscellaneous"))

    assert result == {"id": "c42", "name": "Miscellaneous"}
    assert mock_http.post.call_args.args[0].endswith("/budgets/b1/categories")
    sent_json = mock_http.post.call_args.kwargs["json"]
    assert sent_json == {"category": {"name": "Miscellaneous", "category_group_id": "g1"}}


# ---------------------------------------------------------------------------
# set_category_budgeted / get_accounts
# ---------------------------------------------------------------------------


def test_set_category_budgeted_patches_month_category_in_milliunits() -> None:
    """set_category_budgeted should PATCH {category: {budgeted: milliunits}} for that month."""
    payload = {"data": {"category": {"id": "c1", "budgeted": 1890000}}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.set_category_budgeted("b1", "2026-09-01", "c1", 1890.0))
    http = ctx.__aenter__.return_value
    assert result == {"id": "c1", "budgeted": 1890000}
    assert http.patch.call_args.args[0].endswith("/budgets/b1/months/2026-09-01/categories/c1")
    assert http.patch.call_args.kwargs["json"] == {"category": {"budgeted": 1890000}}


def test_set_category_budgeted_rounds_cents_exactly() -> None:
    """Float amounts like 111.32 must become exactly 111320 milliunits (no 111319)."""
    payload = {"data": {"category": {"id": "c1"}}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            asyncio.run(client.set_category_budgeted("b1", "current", "c1", 111.32))
    sent = ctx.__aenter__.return_value.patch.call_args.kwargs["json"]
    assert sent == {"category": {"budgeted": 111320}}


def test_get_accounts_skips_deleted_and_converts_balances() -> None:
    """get_accounts returns open and closed (not deleted) accounts with euro balances."""
    payload = {
        "data": {
            "accounts": [
                {
                    "id": "a1",
                    "name": "Checking",
                    "type": "checking",
                    "on_budget": True,
                    "closed": False,
                    "deleted": False,
                    "balance": 1250000,
                    "cleared_balance": 1250000,
                    "uncleared_balance": 0,
                },
                {
                    "id": "a2",
                    "name": "Old",
                    "type": "savings",
                    "on_budget": True,
                    "closed": False,
                    "deleted": True,
                    "balance": 0,
                    "cleared_balance": 0,
                    "uncleared_balance": 0,
                },
            ]
        }
    }
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.get_accounts("b1"))
    assert result == [
        {
            "id": "a1",
            "name": "Checking",
            "type": "checking",
            "on_budget": True,
            "closed": False,
            "balance": 1250.0,
            "cleared_balance": 1250.0,
            "uncleared_balance": 0.0,
        },
    ]


# ---------------------------------------------------------------------------
# create_transactions
# ---------------------------------------------------------------------------


def test_create_transactions_posts_milliunits_and_reports_duplicates() -> None:
    """create_transactions should POST cleared transactions in milliunits and summarise."""
    payload = {
        "data": {
            "transaction_ids": ["t1"],
            "duplicate_import_ids": ["dup-1"],
            "transactions": [{"id": "t1"}],
        }
    }
    mock_resp = _mock_response(payload)
    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)
    items = [
        {
            "date": "2026-07-01",
            "amount": -3500.0,
            "payee_name": "Jane Doe",
            "memo": "Salary",
            "category_id": "c1",
            "import_id": "q-1",
        },
        {"date": "2026-07-01", "amount": 4321.0, "payee_name": "Acme Corp", "import_id": "dup-1"},
    ]

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.create_transactions("b1", "a1", items))

    assert result == {"created": 1, "transaction_ids": ["t1"], "duplicate_import_ids": ["dup-1"]}
    assert mock_http.post.call_args.args[0].endswith("/budgets/b1/transactions")
    sent = mock_http.post.call_args.kwargs["json"]["transactions"]
    assert sent[0] == {
        "account_id": "a1",
        "date": "2026-07-01",
        "amount": -3500000,
        "payee_name": "Jane Doe",
        "memo": "Salary",
        "category_id": "c1",
        "import_id": "q-1",
        "cleared": "cleared",
        "approved": True,
    }
    assert sent[1] == {
        "account_id": "a1",
        "date": "2026-07-01",
        "amount": 4321000,
        "payee_name": "Acme Corp",
        "import_id": "dup-1",
        "cleared": "cleared",
        "approved": True,
    }


# ---------------------------------------------------------------------------
# error reporting
# ---------------------------------------------------------------------------


def test_api_error_includes_ynab_detail() -> None:
    """A 4xx from YNAB must surface YNAB's error detail, not just the status code."""
    error = {"error": {"id": "400", "name": "bad_request", "detail": "payee name is reserved"}}
    mock_resp = _mock_response(error, status_code=400)
    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)
    items = [{"date": "2026-07-01", "amount": 1.0, "payee_name": "X"}]

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            with pytest.raises(RuntimeError, match="400.*payee name is reserved"):
                asyncio.run(client.create_transactions("b1", "a1", items))


def test_api_error_with_non_json_body_uses_raw_text() -> None:
    """A gateway error page (non-JSON) must still raise with the raw body text."""
    mock_resp = MagicMock()
    mock_resp.status_code = 502
    mock_resp.json.side_effect = ValueError("not json")
    mock_resp.text = "Bad Gateway"
    ctx = _async_client_returning(None)
    ctx.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            with pytest.raises(RuntimeError, match="502: Bad Gateway"):
                asyncio.run(client.get_budgets())


# ---------------------------------------------------------------------------
# approve_transactions
# ---------------------------------------------------------------------------


def test_approve_transactions_bulk_patches_approved_flag() -> None:
    """approve_transactions should PATCH all ids at once with approved=True."""
    payload = {"data": {"transaction_ids": ["t1", "t2"], "transactions": []}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(client.approve_transactions("b1", ["t1", "t2"]))
    http = ctx.__aenter__.return_value
    assert result == {"approved": 2}
    assert http.patch.call_args.args[0].endswith("/budgets/b1/transactions")
    assert http.patch.call_args.kwargs["json"] == {
        "transactions": [{"id": "t1", "approved": True}, {"id": "t2", "approved": True}]
    }


def test_approve_transactions_empty_list_makes_no_call() -> None:
    """Nothing to approve must not hit the API."""
    with patch("httpx.AsyncClient") as mock_client:
        result = asyncio.run(client.approve_transactions("b1", []))
    mock_client.assert_not_called()
    assert result == {"approved": 0}


def test_set_transaction_categories_bulk_patches_category_ids() -> None:
    """All category changes go in one PATCH; None clears a category."""
    payload = {"data": {"transaction_ids": ["t1", "t2"], "transactions": []}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(
                client.set_transaction_categories("b1", [("t1", "c1"), ("t2", None)])
            )
    http = ctx.__aenter__.return_value
    assert result == ["t1", "t2"]
    assert http.patch.call_args.args[0].endswith("/budgets/b1/transactions")
    assert http.patch.call_args.kwargs["json"] == {
        "transactions": [{"id": "t1", "category_id": "c1"}, {"id": "t2", "category_id": None}]
    }


def test_set_transaction_categories_empty_list_makes_no_call() -> None:
    """Nothing to change must not hit the API."""
    with patch("httpx.AsyncClient") as mock_client:
        result = asyncio.run(client.set_transaction_categories("b1", []))
    mock_client.assert_not_called()
    assert result == []


def test_update_category_patches_only_given_fields() -> None:
    """Renaming sends the name; moving sends the group; nothing else."""
    payload = {"data": {"category": {"id": "c1", "name": "Pets", "category_group_id": "g2"}}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            result = asyncio.run(
                client.update_category("b1", "c1", name="Pets", category_group_id="g2")
            )
    http = ctx.__aenter__.return_value
    assert result["name"] == "Pets"
    assert http.patch.call_args.args[0].endswith("/budgets/b1/categories/c1")
    assert http.patch.call_args.kwargs["json"] == {
        "category": {"name": "Pets", "category_group_id": "g2"}
    }
    with patch("httpx.AsyncClient", return_value=_async_client_returning(payload)) as mocked:
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            asyncio.run(client.update_category("b1", "c1", name="Pets"))
    sent = mocked.return_value.__aenter__.return_value.patch.call_args.kwargs["json"]
    assert sent == {"category": {"name": "Pets"}}


def test_update_category_move_only_sends_the_group() -> None:
    """Moving without renaming leaves the name out of the request."""
    payload = {"data": {"category": {"id": "c1"}}}
    ctx = _async_client_returning(payload)
    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            asyncio.run(client.update_category("b1", "c1", category_group_id="g2"))
    sent = ctx.__aenter__.return_value.patch.call_args.kwargs["json"]
    assert sent == {"category": {"category_group_id": "g2"}}
