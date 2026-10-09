# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for client.py — a failure on the way to YNAB, and what the agent is told about it."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from avenir_mcp import client, retry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _answering(
    *answers: httpx.Response | Exception,
) -> tuple[httpx.MockTransport, list[httpx.Request]]:
    """Give a transport that answers each request in turn, and the list of requests it saw."""
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        answer = answers[len(seen) - 1]
        if isinstance(answer, Exception):
            raise answer
        return answer

    return httpx.MockTransport(handle), seen


async def _instantly(_seconds: float) -> None:
    """Stand in for asyncio.sleep so a test of the retries takes no time."""


def _sent(method: str, transport: httpx.MockTransport, clock: float = 1000.0) -> Any:
    """Send one request of *method* to /plans through *transport*, with the clock stopped."""
    with (
        patch.dict("os.environ", {"YNAB_API_KEY": "tok"}),
        patch("avenir_mcp.client.time.monotonic", return_value=clock),
    ):
        return asyncio.run(
            client._request(  # pylint: disable=protected-access
                method, "/plans", transport=transport, sleep=_instantly
            )
        )


# ---------------------------------------------------------------------------
# A 429: how long YNAB asks to be left alone
# ---------------------------------------------------------------------------


def test_a_429_that_says_when_to_come_back_pauses_for_exactly_that_long() -> None:
    """YNAB's Retry-After sets the pause: 120 seconds, said to the agent as two minutes."""
    transport, seen = _answering(httpx.Response(429, headers={"Retry-After": "120"}))

    with pytest.raises(RuntimeError, match="200 requests per hour.*2 minutes"):
        _sent("get", transport)

    assert len(seen) == 1
    assert client.PACE.paused_until == 1000.0 + 120.0


def test_a_429_that_says_nothing_pauses_for_ten_minutes() -> None:
    """Without a Retry-After the pause is avenir-mcp's own ten minutes, as before."""
    transport, _seen = _answering(httpx.Response(429))

    with pytest.raises(RuntimeError, match="10 minutes"):
        _sent("get", transport)

    assert client.PACE.paused_until == 1000.0 + 600.0


# ---------------------------------------------------------------------------
# Transient failures: what is sent again, and what is never sent again
# ---------------------------------------------------------------------------


def test_a_read_that_hits_a_gateway_error_is_sent_again() -> None:
    """A 503 then a 200 on a read: the body comes back after two requests."""
    plans: Any = {"data": {"plans": []}}
    transport, seen = _answering(httpx.Response(503), httpx.Response(200, json=plans))

    assert _sent("get", transport) == plans
    assert len(seen) == 2


def test_a_read_that_never_gets_through_says_nothing_was_changed() -> None:
    """Three timeouts on a read raise YnabUnavailable, naming the cause and what to do."""
    transport, seen = _answering(*[httpx.ReadTimeout("no answer")] * 3)

    with pytest.raises(retry.YnabUnavailable) as raised:
        _sent("get", transport)

    assert str(raised.value) == (
        "YNAB could not be reached after 3 attempts (ReadTimeout: no answer). "
        "Nothing was changed. Try again in a few minutes."
    )
    assert len(seen) == 3


def test_a_write_that_got_no_answer_is_sent_once_and_left_unknown() -> None:
    """A POST that timed out while waiting is never repeated: YNAB may have applied it."""
    transport, seen = _answering(httpx.ReadTimeout("no answer"))

    with pytest.raises(retry.YnabUnavailable) as raised:
        _sent("post", transport)

    assert str(raised.value) == (
        "The request reached YNAB but no answer came back (ReadTimeout: no answer): the "
        "change may or may not be applied. Check with find_transactions / "
        "get_category_balances before trying again; do not repeat it blindly."
    )
    assert len(seen) == 1


def test_a_write_whose_connection_was_refused_is_sent_again() -> None:
    """A POST that never left is safe to send again: the second try succeeds."""
    transport, seen = _answering(httpx.ConnectError("refused"), httpx.Response(200, json={"a": 1}))

    assert _sent("post", transport) == {"a": 1}
    assert len(seen) == 2


def test_no_httpx_error_ever_leaves_the_client() -> None:
    """Whatever httpx raises becomes a RuntimeError an agent can read and relay."""
    transport, _seen = _answering(*[httpx.ConnectError("refused")] * 3)

    with pytest.raises(RuntimeError) as raised:
        _sent("get", transport)

    assert not isinstance(raised.value, httpx.HTTPError)


def test_every_try_takes_a_request_from_the_hours_budget() -> None:
    """A read sent three times counts three times against the 180 of the rolling hour."""
    transport, _seen = _answering(*[httpx.ReadTimeout("no answer")] * 3)

    with pytest.raises(retry.YnabUnavailable):
        _sent("get", transport)

    assert len(client.PACE.sent) == 3


@pytest.mark.parametrize("status", [400, 404, 409])
def test_a_refusal_is_sent_once_and_carries_ynabs_detail(status: int) -> None:
    """YNAB read the request and refused it: its own detail comes back, after one request."""
    body = {"error": {"id": str(status), "name": "refused", "detail": "no such plan"}}
    transport, seen = _answering(httpx.Response(status, json=body))

    with pytest.raises(RuntimeError, match=f"YNAB {status}: no such plan"):
        _sent("get", transport)

    assert len(seen) == 1


def test_a_401_says_the_token_has_to_be_made_again() -> None:
    """A 401 is not a transient failure: the answer says how to get a working token."""
    body = {"error": {"id": "401", "name": "unauthorized", "detail": "Unauthorized"}}
    transport, seen = _answering(httpx.Response(401, json=body))

    with pytest.raises(RuntimeError) as raised:
        _sent("get", transport)

    assert str(raised.value) == (
        "YNAB 401: the token is invalid or was revoked; create a new Personal Access "
        "Token in YNAB's settings."
    )
    assert len(seen) == 1


def test_a_gateway_error_page_still_there_on_the_last_try_raises_with_its_text() -> None:
    """A 502 answered three times is YNAB's answer in the end, raw body text and all."""
    transport, seen = _answering(*[httpx.Response(502, text="Bad Gateway")] * 3)

    with pytest.raises(RuntimeError, match="502: Bad Gateway"):
        _sent("get", transport)

    assert len(seen) == 3
