"""Shared pytest fixtures for ynab tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from avenir_mcp import client, server


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    """Reset the in-memory delta-sync cache before every test."""
    client._CACHE.clear()  # pylint: disable=protected-access
    client.PACE.reset()


@pytest.fixture(autouse=True)
def writes_enabled() -> Iterator[None]:
    """Start every test with write tools exposed, whatever an earlier test configured."""
    server.configure(enable_writes=True)
    yield
    server.configure(enable_writes=True)
