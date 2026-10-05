# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""What registries and search read about avenir-mcp agrees with the code, and with YNAB's rules."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

from avenir_mcp import __version__

ROOT = Path(__file__).resolve().parent.parent
SERVER = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_the_registry_entry_names_the_package_and_version_pypi_has() -> None:
    """The MCP registry lists the PyPI package this repository builds, at this version."""
    [package] = SERVER["packages"]
    assert package["registryType"] == "pypi"
    assert package["identifier"] == PROJECT["name"]
    assert SERVER["version"] == package["version"] == __version__
    assert package["transport"] == {"type": "stdio"}


def test_the_readme_proves_the_package_belongs_to_the_registry_name() -> None:
    """PyPI ownership is checked by an `mcp-name:` line in the README PyPI shows."""
    assert f"mcp-name: {SERVER['name']}" in README
    assert SERVER["name"] == f"io.github.mathbeal/{PROJECT['name']}"


def test_the_registry_asks_for_the_token_as_a_required_secret() -> None:
    """A client installing from the registry prompts for YNAB_API_KEY and keeps it secret."""
    variables = {v["name"]: v for v in SERVER["packages"][0]["environmentVariables"]}
    assert variables["YNAB_API_KEY"]["isRequired"] is True
    assert variables["YNAB_API_KEY"]["isSecret"] is True


def test_the_typed_classifier_is_backed_by_the_marker_the_package_ships() -> None:
    """`Typing :: Typed` promises the PEP 561 marker, without which mypy ignores the hints."""
    marker = ROOT / "avenir_mcp" / "py.typed"
    assert "Typing :: Typed" in PROJECT["classifiers"]
    assert marker.is_file(), "the classifier promises avenir_mcp/py.typed"
    assert marker.read_bytes() == b"", "the marker is empty: the whole package is typed"


def test_the_descriptions_fit_on_one_line_and_name_ynab() -> None:
    """Short enough for registries' cards, and findable by the word people search for."""
    for description in (SERVER["description"], PROJECT["description"]):
        assert len(description) <= 100, description
        assert "YNAB" in description
    assert "ynab" in PROJECT["keywords"]


@pytest.mark.ynab_terms
def test_no_name_starts_with_ynab_as_ynab_forbids() -> None:
    """YNAB's API terms: a name may say "YNAB" only after "for" ("Tools for YNAB")."""
    names = [PROJECT["name"], SERVER["name"], README.splitlines()[0]]
    for name in names:
        for match in re.finditer(r"ynab|you need a budget", name, flags=re.IGNORECASE):
            assert re.search(r"\bfor\s+$", name[: match.start()], flags=re.IGNORECASE), name
