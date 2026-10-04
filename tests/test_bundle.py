# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The Claude Desktop extension installs the release it names, read-only until asked."""

from __future__ import annotations

import importlib.util
import json
import re
import tomllib
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

from avenir_mcp import __version__

if TYPE_CHECKING:
    from collections.abc import Mapping

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "mcpb"
MANIFEST: dict[str, object] = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
PROJECT = tomllib.loads((BUNDLE / "pyproject.toml").read_text(encoding="utf-8"))
LAUNCHER = BUNDLE / "src" / "server.py"
# The one version of the packing tool, in the justfile and in both workflows: two
# versions would give two verdicts on the same manifest.
PACKER = "@anthropic-ai/mcpb@2.1.2"


def _server() -> Mapping[str, object]:
    """The manifest's `server` object, which says how Claude Desktop starts avenir-mcp."""
    server = MANIFEST["server"]
    assert isinstance(server, dict)
    return server


def _environment() -> Mapping[str, str]:
    """The environment the manifest asks Claude Desktop to start the server with."""
    config = _server()["mcp_config"]
    assert isinstance(config, dict)
    environment = config["env"]
    assert isinstance(environment, dict)
    return environment


def _setting(name: str) -> Mapping[str, object]:
    """One field of `user_config`: what the install dialog asks the reader for."""
    settings = MANIFEST["user_config"]
    assert isinstance(settings, dict)
    setting = settings[name]
    assert isinstance(setting, dict)
    return setting


def _launcher() -> ModuleType:
    """The bundle's entry point, loaded from its path: it belongs to no package."""
    spec = importlib.util.spec_from_file_location("avenir_mcp_bundle", LAUNCHER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_bundle_installs_the_release_it_says_it_is() -> None:
    """The extension's version is the package's: otherwise it installs another release."""
    assert MANIFEST["version"] == __version__
    assert PROJECT["project"]["dependencies"] == [f"avenir-mcp=={__version__}"]


def test_the_bundle_asks_for_the_python_the_package_asks_for() -> None:
    """Claude Desktop fetches a Python avenir-mcp runs on, not one its dependencies refuse."""
    package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    required = package["project"]["requires-python"]
    assert PROJECT["project"]["requires-python"] == required
    compatibility = MANIFEST["compatibility"]
    assert isinstance(compatibility, dict)
    runtimes = compatibility["runtimes"]
    assert isinstance(runtimes, dict)
    assert runtimes["python"] == required


def test_claude_desktop_brings_its_own_python_and_resolves_the_dependencies() -> None:
    """The `uv` runtime: nothing is vendored, so one bundle works on every platform."""
    assert _server()["type"] == "uv"
    assert _server()["entry_point"] == "src/server.py"
    assert LAUNCHER.is_file()
    assert not (BUNDLE / "server" / "lib").exists()
    assert not (BUNDLE / "server" / "venv").exists()


def test_the_bundle_carries_no_dependency_of_its_own() -> None:
    """Its only dependency is avenir-mcp, which brings its own, pinned."""
    assert len(PROJECT["project"]["dependencies"]) == 1
    assert "dependency-groups" not in PROJECT


def test_the_token_comes_from_a_setting_claude_desktop_keeps_out_of_sight() -> None:
    """The token is required, masked as it is typed, and never written in the manifest."""
    assert _environment()["YNAB_API_KEY"] == "${user_config.ynab_api_key}"
    token = _setting("ynab_api_key")
    assert token["type"] == "string"
    assert token["sensitive"] is True
    assert token["required"] is True
    assert "default" not in token


def test_the_manifest_holds_no_secret() -> None:
    """Every value the server starts with is a placeholder: nothing to leak in the zip."""
    for name, value in _environment().items():
        assert re.fullmatch(r"\$\{user_config\.[a-z_]+\}", value), f"{name}={value}"


def test_the_extension_is_read_only_until_the_reader_ticks_a_box() -> None:
    """Installing it cannot change a plan: the write tools stay unregistered."""
    assert _environment()["AVENIR_MCP_WRITE"] == "${user_config.allow_changes}"
    box = _setting("allow_changes")
    assert box["type"] == "boolean"
    assert box["default"] is False
    assert box["required"] is False


@pytest.mark.parametrize("ticked", ["true", "True", " TRUE ", "1", "yes", "on"])
def test_a_ticked_box_becomes_the_exact_value_the_server_asks_for(ticked: str) -> None:
    """Claude Desktop writes a checkbox as JSON; AVENIR_MCP_WRITE reads only `1`."""
    environment = {"AVENIR_MCP_WRITE": ticked}
    _launcher().enable_writes(environment)
    assert environment["AVENIR_MCP_WRITE"] == "1"


@pytest.mark.parametrize("value", ["false", "False", "", "0", "no", "off", "oui"])
def test_anything_else_leaves_the_server_read_only(value: str) -> None:
    """An unticked box, or a value nobody expected, changes nothing on a plan."""
    environment = {"AVENIR_MCP_WRITE": value}
    _launcher().enable_writes(environment)
    assert environment["AVENIR_MCP_WRITE"] != "1"


def test_a_missing_setting_leaves_the_server_read_only() -> None:
    """A client that passes no value at all gets the read-only server, not an error."""
    environment: dict[str, str] = {}
    _launcher().enable_writes(environment)
    assert environment.get("AVENIR_MCP_WRITE") != "1"


def test_the_launcher_translates_then_hands_over_to_the_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It adds no behaviour: the environment is fixed, then avenir-mcp runs as always."""
    launcher = _launcher()
    started: list[list[str]] = []
    monkeypatch.setenv("AVENIR_MCP_WRITE", "true")
    monkeypatch.setattr(launcher.server, "main", started.append)
    launcher.main()
    # An empty argv, not the process's: `--version` belongs to the command line.
    assert started == [[]]
    assert launcher.os.environ["AVENIR_MCP_WRITE"] == "1"


def test_the_install_dialog_says_what_the_token_grants_and_what_a_tick_allows() -> None:
    """A reader decides with the dialog in front of them, not with the documentation."""
    for name in ("ynab_api_key", "allow_changes"):
        setting = _setting(name)
        assert setting["title"]
        description = setting["description"]
        assert isinstance(description, str)
        assert len(description) > 80, name
    assert "undo" in str(_setting("allow_changes")["description"]).lower()


def test_the_extension_points_at_the_project_rather_than_describing_itself_twice() -> None:
    """Its links are the package's, so a reader lands on the documentation that is kept."""
    package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    urls = package["project"]["urls"]
    assert MANIFEST["homepage"] == urls["Documentation"]
    assert MANIFEST["documentation"] == f"{urls['Documentation']}getting-started/install/"
    assert MANIFEST["support"] == urls["Issues"]
    assert MANIFEST["license"] == package["project"]["license"]
    assert MANIFEST["description"] == package["project"]["description"]


def test_the_tools_are_read_from_the_running_server_not_listed_by_hand() -> None:
    """A hand-written list would drift, and would hide which tools a tick adds."""
    assert MANIFEST["tools_generated"] is True
    assert "tools" not in MANIFEST


def test_the_icon_is_a_square_png_claude_desktop_can_show() -> None:
    """A relative PNG of 512 pixels: what the packer accepts and the dialog displays."""
    assert MANIFEST["icon"] == "icon.png"
    data = (BUNDLE / "icon.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    assert int.from_bytes(data[16:20]) == int.from_bytes(data[20:24]) == 512


def test_what_a_local_run_leaves_behind_is_neither_zipped_nor_committed() -> None:
    """Running the extension here resolves a lock and an environment: both stay here.

    A lock cannot be committed either: it would have to name a release of avenir-mcp
    that only exists once the tag it comes from is published.
    """
    ignored = (BUNDLE / ".mcpbignore").read_text(encoding="utf-8").split()
    assert {".venv/", "__pycache__/", "uv.lock"} <= set(ignored)
    assert "mcpb/uv.lock" in (ROOT / ".gitignore").read_text(encoding="utf-8").split()


def test_one_pinned_packer_checks_and_packs_the_bundle_everywhere() -> None:
    """A recipe packs it, and wherever a workflow does too it is the same pinned packer.

    Two versions of the packer would give two verdicts on one manifest: what passes
    before a pull request has to be what runs in it and at release.
    """
    recipe = (ROOT / "justfile").read_text(encoding="utf-8")
    assert f"{PACKER} validate mcpb" in recipe
    assert f"{PACKER} pack mcpb" in recipe
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for line in workflow.read_text(encoding="utf-8").splitlines():
            if re.search(r"mcpb (validate|pack) mcpb", line):
                assert PACKER in line, f"{workflow.name}: {line.strip()}"
