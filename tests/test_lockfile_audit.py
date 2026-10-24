# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Every lock file this repository tracks has a known, audited fate in CI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from .repository import ROOT, tracked

if TYPE_CHECKING:
    from pathlib import Path

WORKFLOWS = ROOT / ".github" / "workflows"

# Every lock file this repository tracks, and the command in the `audit` job that reads
# it for a known vulnerability. A lock file missing here is a lock file CI never checks.
AUDITED_LOCKS: dict[Path, str] = {
    ROOT / "uv.lock": "uvx pip-audit --strict --disable-pip -r requirements.txt",
    ROOT / "docs" / "package-lock.json": (
        "npm audit --prefix docs --package-lock-only --audit-level=high"
    ),
}
# plugin/uv.lock still locks fastmcp 4.0.11, a known vulnerability: auditing it today
# would fail every build until the pin moves, which needs a release of avenir-mcp the
# plugin can pin to. Move it to AUDITED_LOCKS in the same change that moves the pin.
UNAUDITED_LOCKS = {ROOT / "plugin" / "uv.lock"}


def _tracked_locks() -> set[Path]:
    """Every `uv.lock` and `package-lock.json` the repository tracks."""
    return {
        *tracked("uv.lock", "**/uv.lock"),
        *tracked("package-lock.json", "**/package-lock.json"),
    }


def test_every_tracked_lock_file_is_named_here() -> None:
    """A new lock file is either audited or named as a known exception, never silent."""
    assert _tracked_locks() == AUDITED_LOCKS.keys() | UNAUDITED_LOCKS


def test_the_audit_job_runs_every_declared_command() -> None:
    """Each lock's command in `AUDITED_LOCKS` actually runs in the `audit` job."""
    jobs = yaml.safe_load((WORKFLOWS / "quality.yml").read_text(encoding="utf-8"))["jobs"]
    commands = [
        line.strip() for step in jobs["audit"]["steps"] for line in step.get("run", "").splitlines()
    ]
    for lock, command in AUDITED_LOCKS.items():
        assert command in commands, f"{lock}: {command}"
