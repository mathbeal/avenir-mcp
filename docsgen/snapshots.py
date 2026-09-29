"""What the snapshot checks of docsgen share: comparing with YNAB, or updating."""

from __future__ import annotations

import argparse


def update_requested(argv: list[str] | None, description: str | None) -> bool:
    """Read the command line of a snapshot check.

    Args:
        argv: The command-line arguments; None for sys.argv.
        description: What the check does, for --help.

    Returns:
        True when --update asks to rewrite the snapshot instead of comparing.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--update", action="store_true", help="rewrite the snapshot")
    return bool(parser.parse_args(argv).update)
