# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for client.py — what an agent reads when YNAB's answer cannot be trusted as is."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from avenir_mcp import client

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(payload: Any, status_code: int = 200) -> MagicMock:
    """Build a mock httpx response that returns *payload* as JSON, with no header."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = payload
    mock_resp.headers = {}
    return mock_resp


def _client_for(mock_resp: Any, method: str) -> MagicMock:
    """An httpx.AsyncClient mock whose *method* (get/post) answers with *mock_resp*."""
    ctx = MagicMock()
    mock_http = AsyncMock()
    setattr(mock_http, method, AsyncMock(return_value=mock_resp))
    ctx.__aenter__ = AsyncMock(return_value=mock_http)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


# ---------------------------------------------------------------------------
# A 4xx/5xx body: YNAB's own detail surfaces, not just the status code
# ---------------------------------------------------------------------------


def test_api_error_includes_ynab_detail() -> None:
    """A 4xx from YNAB must surface YNAB's error detail, not just the status code."""
    error = {"error": {"id": "400", "name": "bad_request", "detail": "payee name is reserved"}}
    mock_resp = _mock_response(error, status_code=400)
    ctx = _client_for(mock_resp, "post")
    items = [{"date": "2026-07-01", "amount": 1.0, "payee_name": "X"}]

    with patch("httpx.AsyncClient", return_value=ctx):
        with patch.dict("os.environ", {"YNAB_API_KEY": "tok"}):
            with pytest.raises(RuntimeError, match="400.*payee name is reserved"):
                asyncio.run(client.create_transactions("b1", "a1", items))


# ---------------------------------------------------------------------------
# A body that cannot be read: no JSONDecodeError, DecodingError or AttributeError leaks
# ---------------------------------------------------------------------------


def test_a_success_body_that_is_not_json_raises_a_readable_error() -> None:
    """A 200 with a non-JSON body (captive portal, proxy) never leaks a raw JSONDecodeError."""
    mock_resp = _mock_response(None)
    mock_resp.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
    ctx = _client_for(mock_resp, "get")

    with (
        patch("httpx.AsyncClient", return_value=ctx),
        patch.dict("os.environ", {"YNAB_API_KEY": "t"}),
    ):
        with pytest.raises(RuntimeError, match="could not be read"):
            asyncio.run(client.get_plans())


def test_a_corrupted_body_on_a_write_says_it_was_probably_applied() -> None:
    """A write's answer said success; a body that cannot be decoded still probably landed."""
    mock_resp = _mock_response(None)
    mock_resp.json.side_effect = httpx.DecodingError("bad gzip")
    ctx = _client_for(mock_resp, "post")
    items = [{"date": "2026-07-01", "amount": 1.0, "payee_name": "X"}]

    with (
        patch("httpx.AsyncClient", return_value=ctx),
        patch.dict("os.environ", {"YNAB_API_KEY": "t"}),
    ):
        with pytest.raises(RuntimeError, match="probably applied"):
            asyncio.run(client.create_transactions("b1", "a1", items))


def test_an_error_body_shaped_as_a_json_array_falls_back_to_the_raw_text() -> None:
    """A 4xx body that is valid JSON but not an object never raises AttributeError on .get."""
    mock_resp = _mock_response(["Service Unavailable"], status_code=400)
    mock_resp.text = '["Service Unavailable"]'
    ctx = _client_for(mock_resp, "get")

    with (
        patch("httpx.AsyncClient", return_value=ctx),
        patch.dict("os.environ", {"YNAB_API_KEY": "t"}),
    ):
        with pytest.raises(RuntimeError, match=r"400.*Service Unavailable"):
            asyncio.run(client.get_plans())


def test_an_error_body_with_a_null_error_key_falls_back_to_the_raw_text() -> None:
    """{"error": null} is valid JSON with the documented key absent of its object shape."""
    mock_resp = _mock_response({"error": None}, status_code=400)
    mock_resp.text = '{"error": null}'
    ctx = _client_for(mock_resp, "get")

    with (
        patch("httpx.AsyncClient", return_value=ctx),
        patch.dict("os.environ", {"YNAB_API_KEY": "t"}),
    ):
        with pytest.raises(RuntimeError, match=r'400.*\{"error": null\}'):
            asyncio.run(client.get_plans())


class _BrokenGzipResponse:
    """A response whose body is corrupted enough that decoding it fails however it is read.

    A real gzip failure behaves this way: decoding the bytes happens once, so .text
    raises the same way .json() does.
    """

    status_code = 502
    headers: dict[str, str] = {}

    def json(self) -> Any:
        """Fail to decode, as a corrupted gzip body would."""
        raise httpx.DecodingError("bad gzip")

    @property
    def text(self) -> str:
        """Fail the same way .json() does: the same bytes, decoded once."""
        raise httpx.DecodingError("bad gzip")


def test_an_error_body_undecodable_even_as_text_falls_back_to_a_placeholder() -> None:
    """A gateway's body corrupted enough that even .text fails still raises a readable error."""
    ctx = _client_for(_BrokenGzipResponse(), "get")

    with (
        patch("httpx.AsyncClient", return_value=ctx),
        patch.dict("os.environ", {"YNAB_API_KEY": "t"}),
    ):
        with pytest.raises(RuntimeError, match="502: <body could not be decoded>"):
            asyncio.run(client.get_plans())
