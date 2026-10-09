# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Tests for retry.py — which failed YNAB requests may leave again, and after how long."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx
import pytest

from avenir_mcp import retry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ynab(
    *answers: httpx.Response | Exception,
) -> tuple[Callable[[], Awaitable[httpx.Response]], list[object]]:
    """Give a send that answers each try in turn, and the list of what it has handed out."""
    given: list[object] = []

    async def send() -> httpx.Response:
        answer = answers[len(given)]
        given.append(answer)
        if isinstance(answer, Exception):
            raise answer
        return answer

    return send, given


def _waits(allowed: int = 5) -> tuple[Callable[[float], Awaitable[None]], list[float]]:
    """Give a stand-in for asyncio.sleep that records its waits and refuses to wait forever."""
    seconds: list[float] = []

    async def sleep(wait: float) -> None:
        seconds.append(wait)
        assert len(seconds) <= allowed, "the retries never stopped"

    return sleep, seconds


def _full() -> float:
    """Put every wait at the far end of its window, so the window itself is measured."""
    return 1.0


def _none() -> float:
    """Put every wait at the near end of its window."""
    return 0.0


# ---------------------------------------------------------------------------
# decide: what may be sent again
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", [502, 503, 504])
def test_a_read_is_sent_again_when_a_gateway_is_out(status: int) -> None:
    """A 502, 503 or 504 on a GET is a gateway momentarily out: the read goes again."""
    assert retry.decide("get", status, 1, _full) == 0.5


@pytest.mark.parametrize("status", [200, 400, 401, 403, 404, 409, 429, 500])
def test_an_answer_ynab_read_is_never_sent_again(status: int) -> None:
    """YNAB read the request: a refusal, a success or a 429 is never sent a second time."""
    assert retry.decide("get", status, 1, _full) is None


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
@pytest.mark.parametrize("status", [502, 503, 504])
def test_a_write_is_never_sent_again_after_a_gateway_error(method: str, status: int) -> None:
    """A write that reached a gateway may have been applied: a 5xx never sends it twice."""
    assert retry.decide(method, status, 1, _full) is None


@pytest.mark.parametrize(
    "failure",
    [
        httpx.ConnectError("refused"),
        httpx.ConnectTimeout("too long"),
        httpx.ReadTimeout("no answer"),
        httpx.ReadError("cut"),
        httpx.RemoteProtocolError("garbled"),
    ],
)
def test_a_read_is_sent_again_after_any_transport_failure(failure: Exception) -> None:
    """Nothing changes when a read is repeated, so every transport failure is worth a try."""
    assert retry.decide("get", failure, 1, _full) == 0.5


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
@pytest.mark.parametrize(
    "failure", [httpx.ConnectError("refused"), httpx.ConnectTimeout("too long")]
)
def test_a_write_that_never_left_is_sent_again(method: str, failure: Exception) -> None:
    """A connection that was never made proves YNAB saw nothing: the write may go again."""
    assert retry.decide(method, failure, 1, _full) == 0.5


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
@pytest.mark.parametrize(
    "failure",
    [httpx.ReadTimeout("no answer"), httpx.ReadError("cut"), httpx.RemoteProtocolError("garbled")],
)
def test_a_sent_write_is_never_sent_again(method: str, failure: Exception) -> None:
    """Once a write has left, YNAB may have applied it: repeating it would duplicate it."""
    assert retry.decide(method, failure, 1, _full) is None


def test_three_tries_in_all_and_no_more() -> None:
    """The third try is the last: nothing is sent a fourth time, whatever failed."""
    assert retry.ATTEMPTS == 3
    assert retry.decide("get", 503, 2, _full) == 1.0
    assert retry.decide("get", 503, 3, _full) is None


# ---------------------------------------------------------------------------
# decide: how long to wait
# ---------------------------------------------------------------------------


def test_the_window_doubles_after_each_failure() -> None:
    """The first failure waits within half a second, the second within one second."""
    assert retry.decide("get", 503, 1, _full) == 0.5
    assert retry.decide("get", 503, 2, _full) == 1.0


def test_the_wait_falls_anywhere_in_its_window() -> None:
    """Full jitter: the wait is the whole window at one end and nothing at the other."""
    assert retry.decide("get", 503, 1, _none) == 0.0
    assert retry.decide("get", 503, 1, lambda: 0.25) == 0.125


def test_the_window_keeps_doubling_and_is_bounded_by_the_last_try(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing caps the window: only the last try does, by asking for no wait at all."""
    monkeypatch.setattr(retry, "ATTEMPTS", 5)
    windows = [retry.decide("get", 503, attempt, _full) for attempt in range(1, 6)]
    assert windows == [0.5, 1.0, 2.0, 4.0, None]


def test_a_wait_without_a_jitter_of_its_own_stays_in_its_window() -> None:
    """Left to itself, decide draws the wait between nothing and the whole window."""
    draws = [retry.decide("get", 503, 1) for _ in range(50)]
    assert all(delay is not None and 0.0 <= delay < 0.5 for delay in draws)


# ---------------------------------------------------------------------------
# What the agent is told
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
def test_a_write_that_got_no_answer_may_have_been_applied(method: str) -> None:
    """A write lost after it left may have landed: nobody can say it did not."""
    assert retry.landed(method, httpx.ReadTimeout("no answer")) is True


@pytest.mark.parametrize(
    "method, failure",
    [
        ("get", httpx.ReadTimeout("no answer")),
        ("post", httpx.ConnectError("refused")),
        ("post", httpx.ConnectTimeout("too long")),
    ],
)
def test_nothing_landed_when_the_read_or_the_connection_is_the_one_that_failed(
    method: str, failure: Exception
) -> None:
    """A read changes nothing, and a connection never made carried nothing to YNAB."""
    assert retry.landed(method, failure) is False


def test_an_unreachable_ynab_says_nothing_was_changed() -> None:
    """A read that never got through says so, names the cause, and invites a later try."""
    assert retry.no_answer("get", httpx.ConnectError("nothing listening"), 3) == (
        "YNAB could not be reached after 3 attempts (ConnectError: nothing listening). "
        "Nothing was changed. Try again in a few minutes."
    )


def test_a_lost_write_says_what_to_check_before_trying_again() -> None:
    """A write with no answer tells the agent to look, not to repeat and duplicate."""
    assert retry.no_answer("post", httpx.ReadTimeout("no answer"), 1) == (
        "The request reached YNAB but no answer came back (ReadTimeout: no answer): the "
        "change may or may not be applied. Check with find_transactions / "
        "get_category_balances before trying again; do not repeat it blindly."
    )


def test_a_write_that_never_left_says_nothing_was_changed_either() -> None:
    """A write whose connection was refused every time changed nothing: it says so."""
    assert retry.no_answer("post", httpx.ConnectError("refused"), 3) == (
        "YNAB could not be reached after 3 attempts (ConnectError: refused). "
        "Nothing was changed. Try again in a few minutes."
    )


def test_a_failure_that_says_nothing_is_named_by_its_kind_alone() -> None:
    """Some failures httpx raises carry no message: the cause is then just their kind."""
    assert "(ConnectTimeout)." in retry.no_answer("get", httpx.ConnectTimeout(""), 3)


def test_a_lost_request_is_a_runtime_error_like_any_refusal_by_ynab() -> None:
    """YnabUnavailable derives from RuntimeError, so every caller already handles it."""
    assert issubclass(retry.YnabUnavailable, RuntimeError)


# ---------------------------------------------------------------------------
# answered: the tries themselves
# ---------------------------------------------------------------------------


def test_a_read_that_hits_a_gateway_error_then_succeeds_takes_two_requests() -> None:
    """A 503 then a 200: the read answers 200 after two requests and one wait."""
    send, sent = _ynab(httpx.Response(503), httpx.Response(200))
    sleep, waits = _waits()

    response = asyncio.run(retry.answered("get", send, sleep))

    assert response.status_code == 200
    assert len(sent) == 2
    assert len(waits) == 1


def test_a_read_that_never_gets_through_gives_up_after_three_requests() -> None:
    """Three timeouts on a read: three requests, two waits, then the actionable message."""
    send, sent = _ynab(*[httpx.ReadTimeout("no answer")] * 3)
    sleep, waits = _waits()

    with pytest.raises(retry.YnabUnavailable) as raised:
        asyncio.run(retry.answered("get", send, sleep))

    assert str(raised.value) == (
        "YNAB could not be reached after 3 attempts (ReadTimeout: no answer). "
        "Nothing was changed. Try again in a few minutes."
    )
    assert len(sent) == 3
    assert len(waits) == 2


def test_a_write_with_no_answer_is_sent_once_and_told_as_unknown() -> None:
    """A POST that timed out while waiting is not repeated: its outcome is unknown."""
    send, sent = _ynab(httpx.ReadTimeout("no answer"))
    sleep, waits = _waits()

    with pytest.raises(retry.YnabUnavailable) as raised:
        asyncio.run(retry.answered("post", send, sleep))

    assert str(raised.value) == (
        "The request reached YNAB but no answer came back (ReadTimeout: no answer): the "
        "change may or may not be applied. Check with find_transactions / "
        "get_category_balances before trying again; do not repeat it blindly."
    )
    assert len(sent) == 1
    assert not waits


def test_a_write_that_could_not_connect_is_sent_again() -> None:
    """A POST whose connection was refused never reached YNAB, so it goes again."""
    send, sent = _ynab(httpx.ConnectError("refused"), httpx.Response(201))
    sleep, _waited = _waits()

    response = asyncio.run(retry.answered("post", send, sleep))

    assert response.status_code == 201
    assert len(sent) == 2


def test_an_answer_ynab_gave_comes_back_whatever_its_status() -> None:
    """A 400 is YNAB's answer, not a failure to send: it is returned, not retried."""
    send, sent = _ynab(httpx.Response(400))
    sleep, _waited = _waits()

    response = asyncio.run(retry.answered("get", send, sleep))

    assert response.status_code == 400
    assert len(sent) == 1


def test_every_wait_stays_within_the_window_of_its_try() -> None:
    """A read that keeps failing waits twice, in [0, 0.5) then in [0, 1), and no more."""
    send, _sent = _ynab(*[httpx.ReadTimeout("no answer")] * 3)
    sleep, waits = _waits()

    with pytest.raises(retry.YnabUnavailable):
        asyncio.run(retry.answered("get", send, sleep))

    assert 0.0 <= waits[0] < 0.5
    assert 0.0 <= waits[1] < 1.0
    assert len(waits) == 2


# ---------------------------------------------------------------------------
# pause_after: how long YNAB asks to be left alone
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("header", [None, "", "   ", "soon", "in a while", "-120", "1.5"])
def test_an_answer_that_asks_for_nothing_usable_sets_no_pause(header: str | None) -> None:
    """No Retry-After, or one that is not a count of seconds, leaves the pause to us."""
    assert retry.pause_after(header) is None


def test_a_retry_after_in_seconds_sets_the_pause() -> None:
    """Retry-After: 120 means two minutes, and that is how long nothing is sent."""
    assert retry.pause_after("120") == 120.0


@pytest.mark.parametrize("header, expected", [("30", 60.0), ("7200", 3600.0)])
def test_a_retry_after_is_held_between_one_minute_and_one_hour(
    header: str, expected: float
) -> None:
    """A pause shorter than a minute or longer than an hour is brought to the bound."""
    assert retry.pause_after(header) == expected
    assert (retry.MIN_PAUSE, retry.MAX_PAUSE) == (60.0, 3600.0)


def test_a_retry_after_written_as_a_date_is_not_read() -> None:
    """An HTTP-date sets no pause: YNAB documents no Retry-After, so only seconds count."""
    assert retry.pause_after("Fri, 09 Oct 2026 12:05:00 GMT") is None
