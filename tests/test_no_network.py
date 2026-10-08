# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""No test leaves this machine: the autouse fixture of conftest.py closes the way out."""

from __future__ import annotations

import asyncio
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from avenir_mcp import updates

REFUSED = "off this machine"


def test_a_plain_get_is_refused_and_names_what_it_was_asking() -> None:
    """httpx.get cannot reach a remote host, and the error says where it was going."""
    with pytest.raises(RuntimeError, match=REFUSED) as refusal:
        httpx.get(updates.PYPI_URL, timeout=0.1)
    assert updates.PYPI_URL in str(refusal.value)


def test_an_async_client_is_refused_too() -> None:
    """The asynchronous transport, the one the YNAB client uses, is closed as well."""

    async def run() -> None:
        async with httpx.AsyncClient(timeout=0.1) as http:
            await http.get("https://api.ynab.com/v1/budgets")

    with pytest.raises(RuntimeError, match=REFUSED):
        asyncio.run(run())


def test_a_getter_left_to_its_default_is_refused(tmp_path: Path) -> None:
    """Called without a stand-in, latest_version fails loudly instead of asking PyPI."""
    with pytest.raises(RuntimeError, match=REFUSED):
        updates.latest_version(tmp_path / "latest.json", datetime(2026, 10, 1, tzinfo=UTC))


def test_a_stand_in_transport_still_answers() -> None:
    """Only the two real transports are guarded: the tests that drive the app in memory run."""
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json={"ok": True}))
    with httpx.Client(transport=transport, timeout=0.1) as http:
        assert http.get("https://example.invalid/").json() == {"ok": True}


def test_this_machine_stays_reachable() -> None:
    """Loopback goes through: the stand-in YNAB of evals/ is a real server on this machine.

    Nothing listens on port 1, so httpx reports a transport error of its own; what matters
    is that the fixture did not refuse the request before it was attempted.
    """
    with pytest.raises(httpx.TransportError):
        httpx.get("http://127.0.0.1:1/", timeout=0.1)


def test_the_machines_proxy_settings_are_not_read() -> None:
    """no_proxy is set, so a client answers from the environment alone.

    getproxies falls back to the system configuration when the environment says nothing;
    on macOS that fallback calls a framework which aborts a forked process, and
    `just mutate` runs every test in a fork.
    """
    assert urllib.request.getproxies()["no"] == "*"
