# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""What git tracks, which is what a clone, a release archive or a submission carries."""

from __future__ import annotations

import subprocess  # noqa: S404  # nosec B404 - runs git ls-files
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tracked(*paths: str) -> list[Path]:
    """The files git tracks, over the whole repository or under the given paths.

    A file the repository merely holds is not one it carries: an `.gitignore` rule, or a
    local exclude, leaves it out of a clone and out of anything built from one.

    Args:
        paths: Paths to restrict the listing to; the whole repository when none is given.

    Returns:
        The tracked files, as absolute paths, in the order git lists them.
    """
    listed = subprocess.run(  # noqa: S603  # nosec B603 - fixed argument list
        ["git", "ls-files", "-z", "--", *paths],  # noqa: S607 - git from PATH
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return [ROOT / name for name in listed.decode().split("\0") if name]
