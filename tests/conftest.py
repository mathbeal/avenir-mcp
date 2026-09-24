"""Shared pytest fixtures for ynab tests."""

from __future__ import annotations

import pytest

from avenir_mcp import client


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    """Reset the in-memory delta-sync cache before every test."""
    client._CACHE.clear()  # pylint: disable=protected-access
