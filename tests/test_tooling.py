"""The pre-commit hooks run the same tools, the same way, as CI and the justfile."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
HOOKS = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")


def _entries() -> list[str]:
    """The command of every local hook."""
    config = yaml.safe_load(HOOKS)
    return [hook["entry"] for repo in config["repos"] for hook in repo["hooks"] if "entry" in hook]


def _dev_tools() -> set[str]:
    """The names of the dev dependencies, without their versions."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = project["dependency-groups"]["dev"]
    return {re.split(r"[<>=!~\[ ;]", requirement, maxsplit=1)[0] for requirement in requirements}


def test_every_uv_run_hook_is_a_locked_dev_tool() -> None:
    """A hook that runs `uv run X` needs X in the dev group, or it fails for everyone."""
    tools = {entry.split()[2] for entry in _entries() if entry.startswith("uv run ")}
    assert tools
    assert tools <= _dev_tools(), f"not a dev dependency: {sorted(tools - _dev_tools())}"


def test_hooks_lint_and_format_with_ruff_as_ci_does() -> None:
    """Ruff sorts imports and formats; black and isort are gone from the project."""
    entries = _entries()
    assert "uv run ruff check --fix" in entries
    assert "uv run ruff format" in entries
    assert not re.search(r"\b(black|isort)\b", HOOKS)


def test_hooks_hunt_typos_and_audit_workflows_like_the_justfile() -> None:
    """Same commands as the justfile and CI, not older pinned mirrors with other verdicts."""
    recipe = (ROOT / "justfile").read_text(encoding="utf-8")
    for command in (
        "uvx typos",
        "uvx zizmor --persona=regular .github/workflows/",
        "uvx pydoclint==0.10.1 avenir_mcp",
    ):
        assert command in recipe
        assert any(entry.startswith(command) for entry in _entries()), command
    assert "crate-ci/typos" not in HOOKS and "zizmor-pre-commit" not in HOOKS
