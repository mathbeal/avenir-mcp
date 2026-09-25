"""Regenerate the generated parts of the documentation: `python -m docsgen`."""

from __future__ import annotations

from pathlib import Path

from docsgen import examples, reference

DOCS = Path(__file__).resolve().parent.parent / "docs"


def write_all() -> None:
    """Write the reference page and the example snippets."""
    (DOCS / "reference" / "tools.md").parent.mkdir(parents=True, exist_ok=True)
    (DOCS / "reference" / "tools.md").write_text(reference.generate(), encoding="utf-8")
    for name, text in examples.generate().items():
        (DOCS / "snippets" / f"{name}.json").write_text(text, encoding="utf-8")


write_all()
