# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The Claude Desktop extension installs the release it names, read-only until asked."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess  # noqa: S404  # nosec B404 - starts the bundle's own launcher
import sys
import threading
import tomllib
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest
import yaml

from avenir_mcp import __version__

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import IO

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
BUNDLE = ROOT / "mcpb"
# The one name the extension is attached under, so one link always gives the newest
# release. A name carrying the version would give every release its own URL.
ASSET = "avenir-mcp.mcpb"
DOWNLOAD = f"https://github.com/mathbeal/avenir-mcp/releases/latest/download/{ASSET}"
# A file name with a version in it, which no longer names the extension anywhere.
VERSIONED = re.compile(r"avenir-mcp-[^\s\"'`]*\.mcpb")
# Where a reader is sent to the file: the five install pages and the README's button.
DOWNLOAD_PAGES = ("", "fr/", "es/", "de/", "nl/")
MANIFEST: dict[str, object] = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
PROJECT = tomllib.loads((BUNDLE / "pyproject.toml").read_text(encoding="utf-8"))
LAUNCHER = BUNDLE / "src" / "server.py"
# The one version of the packing tool, in the justfile and in both workflows: two
# versions would give two verdicts on the same manifest.
PACKER = "@anthropic-ai/mcpb@2.1.2"
# A launcher that never answers must fail the suite rather than hold it: the handshake
# below takes under a second, and the process is killed well before a runner gives up.
LAUNCH_TIMEOUT = 120.0
# A write tool, so its absence says the server came up read-only.
A_WRITE_TOOL = "move_money"
# What the two requests of the handshake carry.
PARAMS: dict[str, dict[str, object]] = {
    "initialize": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "avenir-mcp's tests", "version": __version__},
    },
    "tools/list": {},
}


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


def _artifact(job: Mapping[str, object], action: str) -> str:
    """The name of the artifact a job's step uploads or downloads with `action`."""
    steps = job["steps"]
    assert isinstance(steps, list)
    names = [step["with"]["name"] for step in steps if action in step.get("uses", "")]
    assert len(names) == 1, f"{action}: {names}"
    assert isinstance(names[0], str)
    return names[0]


def _commands(job: Mapping[str, object]) -> list[str]:
    """Every shell line a job runs, one per line, whatever step it belongs to."""
    steps = job["steps"]
    assert isinstance(steps, list)
    return [line.strip() for step in steps for line in step.get("run", "").splitlines()]


def _install_page(language: str) -> str:
    """The hand-written install page of one language, English for an empty prefix."""
    pages = ROOT / "docs" / "src" / "content" / "docs"
    return (pages / language / "getting-started" / "install.mdx").read_text(encoding="utf-8")


def _launcher() -> ModuleType:
    """The bundle's entry point, loaded from its path: it belongs to no package."""
    spec = importlib.util.spec_from_file_location("avenir_mcp_bundle", LAUNCHER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _environment_claude_desktop_would_pass(box: str | None) -> dict[str, str]:
    """The environment of a fresh install: the manifest's two settings and nothing else.

    Args:
        box: The "Allow changes to your plans" checkbox as Claude Desktop writes it,
            or None for a client that passes no value.

    Returns:
        The environment to start the launcher with.
    """
    # Whatever this machine sets for avenir-mcp is not what a reader's install has.
    environment = {name: value for name, value in os.environ.items() if "AVENIR_MCP" not in name}
    environment["YNAB_API_KEY"] = "not-a-real-token"
    # The handshake must not depend on PyPI answering.
    environment["AVENIR_MCP_NO_UPDATE_CHECK"] = "1"
    if box is not None:
        environment["AVENIR_MCP_WRITE"] = box
    return environment


def _tools_the_launcher_offers(box: str | None) -> list[str]:
    """Start the launcher, speak MCP to it over stdio, and read back the tools it lists.

    This is the handshake Claude Desktop makes, with the launcher started here rather
    than by Claude Desktop's own uv: it says that the file runs and answers on this
    platform, not that uv resolves the pin, which `mcpb pack` and the pin's tests cover.

    Args:
        box: The "Allow changes to your plans" checkbox as Claude Desktop writes it,
            or None for a client that passes no value.

    Returns:
        The names of the tools the server lists, in the order it lists them.

    Raises:
        AssertionError: If the server stops before answering, or names itself something
            other than the release this repository is.
    """
    process = subprocess.Popen(  # noqa: S603  # nosec B603 - the bundle's own launcher
        [sys.executable, str(LAUNCHER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        # stdout belongs to the protocol; the banner and the logs go to stderr.
        stderr=subprocess.DEVNULL,
        env=_environment_claude_desktop_would_pass(box),
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    # The context manager closes the three pipes and waits; the timer makes sure there
    # is something to wait for, whatever the launcher does.
    with process:
        assert process.stdin and process.stdout
        killer = threading.Timer(LAUNCH_TIMEOUT, process.kill)
        killer.start()
        try:
            return _handshake(process.stdin, process.stdout)
        finally:
            killer.cancel()
            process.kill()


def _handshake(to_server: IO[str], from_server: IO[str]) -> list[str]:
    """Initialise the session, then ask for the tools, one JSON object per line.

    Args:
        to_server: The launcher's standard input.
        from_server: The launcher's standard output.

    Returns:
        The names of the tools the server lists.

    Raises:
        AssertionError: If the server stops before answering, or names itself something
            other than the release this repository is.
    """

    def ask(identifier: int, method: str) -> Mapping[str, object]:
        request = {"jsonrpc": "2.0", "id": identifier, "method": method, "params": PARAMS[method]}
        to_server.write(f"{json.dumps(request)}\n")
        to_server.flush()
        for line in from_server:
            answer = json.loads(line)
            if answer.get("id") == identifier:
                result = answer["result"]
                assert isinstance(result, dict), answer
                return result
        raise AssertionError(f"the launcher stopped before answering {method}")

    about = ask(1, "initialize")["serverInfo"]
    assert about == {"name": "avenir-mcp", "version": __version__}, about
    to_server.write(f"{json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'})}\n")
    to_server.flush()
    listed = ask(2, "tools/list")["tools"]
    assert isinstance(listed, list)
    return [tool["name"] for tool in listed]


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
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        for line in workflow.read_text(encoding="utf-8").splitlines():
            if re.search(r"mcpb (validate|pack) mcpb", line):
                assert PACKER in line, f"{workflow.name}: {line.strip()}"


@pytest.mark.parametrize("box", [None, "false", "true"])
def test_the_launcher_starts_and_answers_an_mcp_client(box: str | None) -> None:
    """Started as an installed extension is, it comes up and lists tools, on every platform.

    The unit tests above read the launcher's translation; this one runs the file. It is
    the check that Windows, where nobody develops avenir-mcp, gets too: the suite runs
    there, so a launcher that only starts on a Unix fails the pull request.
    """
    offered = _tools_the_launcher_offers(box)
    assert offered, "the server listed no tool at all"
    assert (A_WRITE_TOOL in offered) is (box == "true")


def test_the_extension_packs_where_a_reader_installs_it() -> None:
    """Packing is checked on Windows as well as Linux: a reader of either opens one file.

    The packer walks the directory and writes a zip; what it does with a path separator
    or a line ending is its business, and the only way to know is to run it there.
    """
    jobs = yaml.safe_load((WORKFLOWS / "quality.yml").read_text(encoding="utf-8"))["jobs"]
    assert set(jobs["bundle"]["strategy"]["matrix"]["os"]) == {"ubuntu-latest", "windows-latest"}
    assert jobs["bundle"]["runs-on"] == "${{ matrix.os }}"


def test_the_release_attaches_the_extension_under_a_name_that_never_changes() -> None:
    """Every release carries the same file name, so one link gives the newest extension.

    The version a file installs stays readable in its manifest (`mcpb info`); in the name
    as well, it would give each release its own URL, and the documentation would have to
    name a release to link to rather than `releases/latest/download`.
    """
    workflow = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
    jobs = yaml.safe_load(workflow)["jobs"]
    packed = [command for command in _commands(jobs["bundle"]) if "pack mcpb" in command]
    uploaded = [command for command in _commands(jobs["bundle-upload"]) if ASSET in command]

    assert packed == [f"npx --yes {PACKER} pack mcpb {ASSET}"]
    assert len(uploaded) == 1
    assert not VERSIONED.search(workflow), VERSIONED.search(workflow)
    # And what `just bundle` writes here is the file a release carries, under that name.
    assert f"pack mcpb dist/{ASSET}" in (ROOT / "justfile").read_text(encoding="utf-8")


@pytest.mark.parametrize("language", DOWNLOAD_PAGES)
def test_every_install_page_offers_the_file_itself_rather_than_the_release_page(
    language: str,
) -> None:
    """A reader downloads the extension from the page, without going through GitHub first.

    The link is `releases/latest/download`, which GitHub answers with the file of the
    newest release, so no page has to name a version.
    """
    page = _install_page(language)
    assert page.count(DOWNLOAD) >= 2, "the download step and the update row both link to it"
    assert not VERSIONED.search(page), VERSIONED.search(page)


def test_the_readme_button_downloads_the_extension_rather_than_opening_a_release() -> None:
    """The README's Claude Desktop button is the same one-click download as the page's."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"]({DOWNLOAD})" in readme
    assert not VERSIONED.search(readme), VERSIONED.search(readme)


def test_what_a_reader_can_check_about_the_file_names_the_file_they_downloaded() -> None:
    """The security page's commands take the name the release attaches, not an older one."""
    assert ASSET in (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert not VERSIONED.search((ROOT / "SECURITY.md").read_text(encoding="utf-8"))


def test_the_job_that_packs_the_extension_cannot_change_the_release() -> None:
    """Packing and attaching are two jobs: only the second holds a token that can write.

    The packer's version is pinned, what it depends on is not. One of those turning
    hostile must find nothing it could rewrite, so the job that runs it is read-only and
    hands the file over; the job that can write to the release runs no third-party code.
    """
    jobs = yaml.safe_load((WORKFLOWS / "publish.yml").read_text(encoding="utf-8"))["jobs"]
    packing, attaching = jobs["bundle"], jobs["bundle-upload"]

    assert packing["permissions"] == {"contents": "read"}
    assert attaching["needs"] == "bundle"
    assert attaching["permissions"] == {"contents": "write"}

    # The packed file is all that crosses from one job to the other.
    assert _artifact(packing, "actions/upload-artifact") == _artifact(
        attaching, "actions/download-artifact"
    )
    for step in attaching["steps"]:
        assert "setup-node" not in step.get("uses", "")
        for command in step.get("run", "").splitlines():
            assert command.startswith("gh release upload "), command
