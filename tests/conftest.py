"""Shared pytest fixtures for ynab tests."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from hypothesis import HealthCheck, settings

from avenir_mcp import client, server

# `just fuzz`: the same properties, many more examples each. What fails is saved in
# .hypothesis/ and replayed, minimised, by the next ordinary run.
settings.register_profile(
    "fuzz",
    max_examples=int(os.getenv("AVENIR_MCP_FUZZ_EXAMPLES", "50000")),
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    """Reset the in-memory delta-sync cache before every test."""
    client._CACHE.clear()  # pylint: disable=protected-access
    client.PACE.reset()


@pytest.fixture(autouse=True)
def no_update_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never ask PyPI from a test: main() would otherwise check for a newer release."""
    monkeypatch.setenv("AVENIR_MCP_NO_UPDATE_CHECK", "1")


@pytest.fixture(autouse=True)
def writes_enabled() -> Iterator[None]:
    """Start every test with write tools exposed, whatever an earlier test configured."""
    server.configure(enable_writes=True)
    yield
    server.configure(enable_writes=True)
