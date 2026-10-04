# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Where the generated documentation goes, and what it contains."""

from __future__ import annotations

from pathlib import Path

from docsgen import api, demo, examples, readme, reference

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "docs" / "src" / "content" / "docs"
SNIPPETS = ROOT / "docs" / "src" / "snippets"
ASSETS = ROOT / ".github" / "assets"
# The site serves its own copy of the demo: a page cannot reach a file outside docs/.
PUBLIC = ROOT / "docs" / "public"


def security() -> str:
    """SECURITY.md as a documentation page: the file stays the single source."""
    body = (ROOT / "SECURITY.md").read_text(encoding="utf-8").split("\n", 1)[1].lstrip()
    front = (
        "---\n"
        "title: Security\n"
        "description: What avenir-mcp can read and change, and how to report a vulnerability.\n"
        "---\n\n"
        ":::note[Generated]\n"
        "Copied from `SECURITY.md` by `python -m docsgen`.\n"
        ":::\n\n"
    )
    return front + body


def generated() -> dict[Path, str]:
    """Every generated file and its expected content."""
    captures = {language: examples.capture_all(language) for language in reference.LANGUAGES}
    files = {
        CONTENT / "project" / "security.md": security(),
        CONTENT / "reference" / "api-coverage.md": api.page(),
    }
    for relative, text in reference.generate(captures).items():
        files[CONTENT / relative] = text
    for language, by_name in captures.items():
        for name, capture in by_name.items():
            files[SNIPPETS / language / f"{name}.json"] = capture.text
    for scheme, svg in readme.charts(captures[""]["forecast"].text).items():
        files[ASSETS / f"forecast-{scheme}.svg"] = svg
    for scheme, svg in readme.net_worth_charts(captures[""]["net_worth"].text).items():
        files[ASSETS / f"networth-{scheme}.svg"] = svg
    for scheme, svg in demo.pictures().items():
        files[ASSETS / f"demo-{scheme}.svg"] = svg
        files[PUBLIC / f"demo-{scheme}.svg"] = svg
    return files


def write_all() -> None:
    """Write every generated file, and remove generated files that no longer exist."""
    files = generated()
    for folder in (
        *(SNIPPETS / lang for lang in reference.LANGUAGES),
        *(CONTENT / lang / "reference" / "tools" for lang in reference.LANGUAGES),
    ):
        if folder.exists():
            for old in folder.iterdir():
                if old.is_file() and old not in files:
                    old.unlink()
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
