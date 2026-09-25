"""Where the generated documentation goes, and what it contains."""

from __future__ import annotations

from pathlib import Path

from docsgen import examples, reference

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "docs" / "src" / "content" / "docs"
SNIPPETS = ROOT / "docs" / "src" / "snippets"


def security() -> str:
    """SECURITY.md as a documentation page: the file stays the single source."""
    body = (ROOT / "SECURITY.md").read_text(encoding="utf-8").split("\n", 1)[1].lstrip()
    front = (
        "---\n"
        "title: Security\n"
        "description: What Avenir can read and change, and how to report a vulnerability.\n"
        "---\n\n"
        ":::note[Generated]\n"
        "Copied from `SECURITY.md` by `python -m docsgen`.\n"
        ":::\n\n"
    )
    return front + body


def generated() -> dict[Path, str]:
    """Every generated file and its expected content."""
    files = {
        CONTENT / "reference" / "tools.md": reference.generate(),
        CONTENT / "security.md": security(),
    }
    for name, text in examples.generate().items():
        files[SNIPPETS / f"{name}.json"] = text
    return files


def write_all() -> None:
    """Write every generated file."""
    for path, text in generated().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
