# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The Claude Code plugin starts the release it names, from its own lock, read-only."""

from __future__ import annotations

import json
import re
import tomllib
from typing import TYPE_CHECKING

import pytest
import yaml

from avenir_mcp import __version__

from .repository import ROOT, tracked

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

WORKFLOWS = ROOT / ".github" / "workflows"
PLUGIN = ROOT / "plugin"
MANIFEST: dict[str, object] = json.loads(
    (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
)
SERVERS: dict[str, object] = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
PROJECT = tomllib.loads((PLUGIN / "pyproject.toml").read_text(encoding="utf-8"))
LOCK = tomllib.loads((PLUGIN / "uv.lock").read_text(encoding="utf-8"))
PACKAGE = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
# The one name the plugin gives its server; a client prefixes the tools with it.
SERVER = "avenir"
# The environment Claude Code expands for the plugin: the folder it unpacked the plugin
# into. The command names no other variable, so nothing of the reader's shell reaches it.
PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"
# What starts the server: the pinned release of `pyproject.toml`, resolved by `uv.lock`
# beside it (`--locked` refuses to start if the two disagree), in the plugin's own folder.
COMMAND = "uv"
ARGUMENTS = ["run", "--locked", "--project", PLUGIN_ROOT, "avenir-mcp"]
# The variable that turns the write tools on. The plugin never sets it: installing it
# cannot change a plan, and a reader who wants to adds it to their own configuration.
WRITE = "AVENIR_MCP_WRITE"
# The one version of the validator, in the justfile and in the workflow: two versions
# would give two verdicts on the same plugin.
VALIDATOR = "@anthropic-ai/claude-code@2.1.308"
# What the plugin directory refuses to carry, and what a Mac or a Windows leaves behind.
SYSTEM_FILES = (".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX")
# Everything the plugin is, so an extra file has to be added here before it ships.
FILES = {
    ".claude-plugin/icon.png",
    ".claude-plugin/plugin.json",
    ".mcp.json",
    "pyproject.toml",
    "uv.lock",
}
# What a local `uv run --project plugin` leaves beside the lock, which git must ignore so
# that it is never committed and never submitted with the plugin.
LEFTOVERS = {".venv", "__pycache__"}
# The five hand-written copies of the release checklist.
LANGUAGES = ("", "fr", "es", "de", "nl")
# A placeholder Claude Code fills from the plugin's settings, and nothing else.
SETTING = re.compile(r"\$\{user_config\.[a-z_]+\}")


def _server() -> Mapping[str, object]:
    """The `.mcp.json` entry that says how Claude Code starts avenir-mcp."""
    servers = SERVERS["mcpServers"]
    assert isinstance(servers, dict)
    server = servers[SERVER]
    assert isinstance(server, dict)
    return server


def _arguments() -> list[str]:
    """The command line the plugin's server is started with, after the executable."""
    arguments = _server()["args"]
    assert isinstance(arguments, list)
    return [str(argument) for argument in arguments]


def _environment() -> Mapping[str, str]:
    """The environment the plugin asks Claude Code to start the server with."""
    environment = _server()["env"]
    assert isinstance(environment, dict)
    return environment


def _setting(name: str) -> Mapping[str, object]:
    """One field of `userConfig`: what the plugin's settings ask the reader for."""
    settings = MANIFEST["userConfig"]
    assert isinstance(settings, dict)
    setting = settings[name]
    assert isinstance(setting, dict)
    return setting


def _locked(name: str) -> Mapping[str, object]:
    """One package of `plugin/uv.lock`, by name.

    Args:
        name: The distribution's name as uv writes it in the lock.

    Returns:
        The package's table.
    """
    found = [package for package in LOCK["package"] if package["name"] == name]
    assert len(found) == 1, f"{name}: {len(found)} entries"
    package = found[0]
    assert isinstance(package, dict)
    return package


def _release_checklist(language: str) -> str:
    """The hand-written development page of one language, English for an empty prefix.

    Args:
        language: The site's prefix for the language, empty for English.

    Returns:
        The page's text.
    """
    pages = ROOT / "docs" / "src" / "content" / "docs"
    return (pages / language / "project" / "development.mdx").read_text(encoding="utf-8")


def _shipped() -> list[Path]:
    """Every file that travels with the plugin: what git tracks under its folder.

    A plugin submitted from a repository holds only what is committed there, so this is
    what git lists, not what the folder happens to contain. A file left untracked, by an
    `.gitignore` or by a local exclude, is missing from the submission and from here.

    Returns:
        The files the plugin is made of, at any depth, in no particular order.
    """
    return tracked(PLUGIN.name)


def test_the_plugin_installs_the_release_it_says_it_is() -> None:
    """The version, the pin and the lock are one release: otherwise it installs another."""
    assert MANIFEST["version"] == __version__
    assert PROJECT["project"]["version"] == __version__
    assert PROJECT["project"]["dependencies"] == [f"avenir-mcp=={__version__}"]
    assert _locked("avenir-mcp")["version"] == __version__


def test_the_lock_was_written_from_the_pin_beside_it() -> None:
    """A pin bumped without `uv lock` would start a release the lock never resolved.

    `--locked` makes Claude Code refuse to start the server in that case; this says so
    before a reader meets it, and `just lock` re-resolves the pin to be sure.
    """
    required = PROJECT["project"]["dependencies"]
    metadata = _locked(PROJECT["project"]["name"])["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["requires-dist"] == [
        {"name": "avenir-mcp", "specifier": required[0].removeprefix("avenir-mcp")}
    ]
    assert LOCK["requires-python"] == PROJECT["project"]["requires-python"]


def test_the_plugin_asks_for_the_python_the_package_asks_for() -> None:
    """A Python avenir-mcp runs on is what uv fetches, not one its dependencies refuse."""
    assert PROJECT["project"]["requires-python"] == PACKAGE["project"]["requires-python"]


def test_the_lock_pins_every_version_underneath_the_release_as_well() -> None:
    """What the badge for a locked launcher is about: one resolution, hashed, reused.

    avenir-mcp pins only `fastmcp`; `httpx`, `pydantic` and the rest are ranges. Without
    this lock, two installs a month apart would run different versions of them.
    """
    packages = LOCK["package"]
    assert len(packages) > 1
    for package in packages:
        if package["name"] == PROJECT["project"]["name"]:
            # The plugin's own folder, which uv never builds and never downloads.
            assert package["source"] == {"virtual": "."}
            continue
        assert package["source"] == {"registry": "https://pypi.org/simple"}
        artefacts = [
            *package.get("wheels", []),
            *([package["sdist"]] if "sdist" in package else []),
        ]
        assert artefacts, package["name"]
        for artefact in artefacts:
            assert artefact["hash"].startswith("sha256:"), package["name"]


def test_the_token_comes_from_a_setting_claude_code_keeps_out_of_sight() -> None:
    """The token is required, marked sensitive, and never written in the plugin."""
    assert _environment()["YNAB_API_KEY"] == "${user_config.ynab_token}"
    token = _setting("ynab_token")
    assert token["type"] == "string"
    assert token["sensitive"] is True
    assert token["required"] is True
    assert "default" not in token


def test_the_settings_say_what_the_token_grants() -> None:
    """A reader decides in the settings dialog, not in the documentation."""
    token = _setting("ynab_token")
    assert token["title"]
    description = token["description"]
    assert isinstance(description, str)
    assert len(description) > 80


def test_the_plugin_holds_no_secret() -> None:
    """Every value the server starts with is a placeholder: nothing to leak in the repository."""
    for name, value in _environment().items():
        assert SETTING.fullmatch(value), f"{name}={value}"


def test_installing_the_plugin_cannot_change_a_plan() -> None:
    """It starts avenir-mcp read-only: the write tools stay unregistered.

    `AVENIR_MCP_WRITE` appears nowhere in the plugin, so no setting and no default can
    turn the write tools on; a reader who wants them sets it in their own configuration.
    """
    assert set(_environment()) == {"YNAB_API_KEY"}
    for path in _shipped():
        assert WRITE not in path.read_bytes().decode("utf-8", "replace"), path


def test_the_server_is_started_from_the_plugin_root_by_uv() -> None:
    """One command, the pinned release, its lock enforced: nothing of the clone is used."""
    assert _server()["command"] == COMMAND
    assert _arguments() == ARGUMENTS


def test_the_plugin_root_is_the_only_path_the_command_expands() -> None:
    """Each path is written in full from `${CLAUDE_PLUGIN_ROOT}`, which Claude Code sets.

    Another variable would be the reader's shell, which says nothing about where the
    plugin was unpacked, and a relative path would be whatever folder they started in.
    """
    for argument in _arguments():
        expanded = re.findall(r"\$\{?[A-Za-z_][A-Za-z_0-9]*\}?", argument)
        assert expanded in ([], [PLUGIN_ROOT]), argument
        assert not argument.startswith(("./", "../")), argument


def test_the_icon_is_a_square_png_the_plugin_directory_accepts() -> None:
    """512 pixels each side, well under its two megabytes, at the path it looks in first.

    The listing takes the icon once, when the plugin is first submitted: it has to be
    committed before that, not added afterwards.
    """
    icon = PLUGIN / ".claude-plugin" / "icon.png"
    assert MANIFEST["icon"] == "./.claude-plugin/icon.png"
    data = icon.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    assert int.from_bytes(data[16:20]) == int.from_bytes(data[20:24]) == 512
    assert len(data) < 2 * 1024 * 1024


def test_the_plugin_points_at_the_project_rather_than_describing_itself_twice() -> None:
    """Its name, text and links are the package's, so a reader lands on the kept pages."""
    urls = PACKAGE["project"]["urls"]
    assert MANIFEST["name"] == PACKAGE["project"]["name"]
    assert MANIFEST["description"] == PACKAGE["project"]["description"]
    assert MANIFEST["license"] == PACKAGE["project"]["license"]
    assert MANIFEST["homepage"] == urls["Documentation"]
    assert MANIFEST["repository"] == urls["Repository"]
    assert MANIFEST["privacyPolicyUrl"] == f"{urls['Documentation']}project/privacy/"


def test_the_privacy_policy_is_a_page_the_site_publishes() -> None:
    """The URL the plugin declares is written here, not a page that may never exist."""
    page = ROOT / "docs" / "src" / "content" / "docs" / "project" / "privacy.mdx"
    assert page.is_file()


def test_the_readme_says_what_the_plugin_runs_contacts_and_writes() -> None:
    """The directory's review reads the README: the plugin's effects are listed there."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Claude Code plugin" in readme
    for stated in (f"{COMMAND} {' '.join(ARGUMENTS[:3])}", "api.ynab.com", "pypi.org"):
        assert stated in readme, stated


def test_the_readme_carries_a_privacy_policy_the_directory_can_find() -> None:
    """A listing needs a privacy policy: the README names one and the manifest links it."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Privacy Policy" in readme
    assert str(MANIFEST["privacyPolicyUrl"]) in readme


def test_the_plugin_is_those_files_and_nothing_else() -> None:
    """Those five files are committed, and no sixth one is: what is submitted is known.

    A file left untracked would be absent from a reader's install, and one added without
    being listed here would ship unnoticed.
    """
    assert {str(path.relative_to(PLUGIN).as_posix()) for path in _shipped()} == FILES


def test_no_file_of_a_desktop_travels_with_the_plugin() -> None:
    """The repository sits in a synchronised folder; the directory refuses such a file."""
    for path in _shipped():
        assert not any(part in SYSTEM_FILES for part in path.relative_to(PLUGIN).parts), path
    assert ".DS_Store" in (ROOT / ".gitignore").read_text(encoding="utf-8").split()


def test_what_a_local_run_leaves_in_the_plugin_stays_there() -> None:
    """`uv run` resolves an environment beside the lock: it is ignored, never committed."""
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    assert {f"{name}/" for name in LEFTOVERS} <= set(ignored)


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_release_checklist_repins_the_plugin(language: str) -> None:
    """A release that leaves the pin behind would install the previous one for everybody.

    Args:
        language: The site's prefix for the language, empty for English.
    """
    page = _release_checklist(language)
    assert "plugin/pyproject.toml" in page
    assert "plugin/uv.lock" in page


def test_one_pinned_validator_checks_the_plugin_here_and_in_ci() -> None:
    """A recipe runs it, and the workflow runs the same version: one verdict, not two."""
    recipe = (ROOT / "justfile").read_text(encoding="utf-8")
    assert f"{VALIDATOR} plugin validate" in recipe
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        for line in workflow.read_text(encoding="utf-8").splitlines():
            if "plugin validate" in line:
                assert VALIDATOR in line, f"{workflow.name}: {line.strip()}"


def test_ci_fails_on_what_the_plugin_directory_would_refuse_or_warn_about() -> None:
    """`--profile directory --strict`: a warning there is a warning on the submission."""
    jobs = yaml.safe_load((WORKFLOWS / "quality.yml").read_text(encoding="utf-8"))["jobs"]
    commands = [
        line.strip()
        for step in jobs["plugin"]["steps"]
        for line in step.get("run", "").splitlines()
    ]
    assert [command for command in commands if "plugin validate" in command] == [
        f"npx --yes {VALIDATOR} plugin validate --profile directory --strict ./plugin"
    ]
    assert "plugin" in jobs["passed"]["needs"]


def test_the_lockfile_job_checks_the_plugin_lock_as_well_as_the_package_lock() -> None:
    """Two locks, one job: a stale plugin lock fails the pull request, not a reader's install."""
    jobs = yaml.safe_load((WORKFLOWS / "quality.yml").read_text(encoding="utf-8"))["jobs"]
    commands = [
        line.strip() for step in jobs["lock"]["steps"] for line in step.get("run", "").splitlines()
    ]
    assert "uv lock --check" in commands
    assert "uv lock --check --project plugin" in commands
