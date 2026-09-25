"""Write the tool, resource and prompt reference from the server itself.

The reference cannot drift from the code: it is generated from what the
server declares, and a test fails when the committed page differs.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client

_KIND = {True: "read", False: "write"}


def _params(schema: dict[str, Any]) -> list[str]:
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    rows = []
    for name, spec in props.items():
        kind = spec.get("type") or " | ".join(
            str(option.get("type", "object")) for option in spec.get("anyOf", [])
        )
        default = "required" if name in required else f"default `{spec.get('default')!r}`"
        rows.append(f"| `{name}` | {kind or 'object'} | {default} |")
    return rows


def _doc(text: str) -> str:
    """The docstring body, without the Args section the parameter table replaces."""
    return text.split("\n\nArgs:")[0].strip()


def _tool_row(tool: Any) -> str:
    ann = tool.annotations
    read = ann.read_only_hint is True
    destructive = "—" if read else ("yes" if ann.destructive_hint else "no")
    summary = (tool.description or "").strip().splitlines()[0]
    return f"| [`{tool.name}`](#{tool.name}) | {_KIND[read]} | {destructive} | {summary} |"


def _tool_section(tool: Any) -> list[str]:
    ann = tool.annotations
    tags = ["read-only" if ann.read_only_hint else "write"]
    if not ann.read_only_hint:
        tags.append("destructive" if ann.destructive_hint else "additive")
        tags.append("idempotent" if ann.idempotent_hint else "not idempotent")
        tags.append("hidden unless `AVENIR_MCP_WRITE=1`")
    lines = ["", f"### `{tool.name}`", "", " · ".join(tags), "", _doc(tool.description or ""), ""]
    rows = _params(tool.input_schema)
    if rows:
        lines += ["| Parameter | Type | |", "|---|---|---|", *rows]
    return lines


def _context_sections(resources: Any, templates: Any, prompts: Any) -> list[str]:
    lines = ["", "## Resources", "", "| URI | Description |", "|---|---|"]
    lines += [f"| `{r.uri}` | {(r.description or '').strip()} |" for r in resources]
    lines += [f"| `{t.uri_template}` | {(t.description or '').strip()} |" for t in templates]
    lines += ["", "## Prompts", "", "| Prompt | Arguments | Description |", "|---|---|---|"]
    for prompt in prompts:
        args = ", ".join(
            f"`{a.name}`" + ("" if a.required else " (optional)") for a in prompt.arguments or []
        )
        lines.append(f"| `{prompt.name}` | {args} | {(prompt.description or '').strip()} |")
    return lines


async def _collect() -> str:
    from avenir_mcp import server  # pylint: disable=import-outside-toplevel

    server.configure(enable_writes=True)
    async with Client(server.mcp) as mcp_client:
        tools = sorted(
            await mcp_client.list_tools(),
            key=lambda t: (t.annotations.read_only_hint is False, t.name),
        )
        resources = await mcp_client.list_resources()
        templates = await mcp_client.list_resource_templates()
        prompts = await mcp_client.list_prompts()
    lines = [
        "---",
        "title: Tools, resources and prompts",
        "description: Every tool, resource and prompt Avenir declares, generated from the server.",
        "sidebar:",
        "  order: 1",
        "---",
        "",
        ":::note[Generated]",
        "This page is generated from the server by `python -m docsgen`; a test fails when it",
        "no longer matches the code.",
        ":::",
        "",
        "## Tools",
        "",
        "| Tool | Kind | Destructive | Summary |",
        "|---|---|---|---|",
        *(_tool_row(tool) for tool in tools),
    ]
    for tool in tools:
        lines += _tool_section(tool)
    lines += _context_sections(resources, templates, prompts)
    return "\n".join(lines) + "\n"


def generate() -> str:
    """The reference page as Markdown."""
    return asyncio.run(_collect())
