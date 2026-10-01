"""Check avenir-mcp the way a client sees it, with the official MCP Inspector.

Starts the demo budget, runs the server over stdio through `npx
@modelcontextprotocol/inspector --cli`, and checks what every client relies on:
the lists of tools, resources and prompts, the portability of the tool schemas
(`--strict`), and one call of each kind. Needs Node.js; run with
`uv run python -m evals.inspector`.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess  # noqa: S404  # nosec B404 - runs npx with a fixed argument list
import sys
import tempfile
from collections.abc import Callable
from typing import Any

from fastmcp import Client

from evals import demo_budget, fake_ynab

INSPECTOR = "@modelcontextprotocol/inspector@2.8.0"


async def _in_process() -> dict[str, int]:
    """Count what the server registers, writes enabled, seen from inside the process.

    Inspector, over stdio, must list the same: the counts are never written by hand.

    Returns:
        How many tools, resources, resource templates and prompts the server offers.
    """
    from avenir_mcp import server  # pylint: disable=import-outside-toplevel

    server.configure(enable_writes=True)
    async with Client(server.mcp) as mcp_client:
        return {
            "tools": len(await mcp_client.list_tools()),
            "resources": len(await mcp_client.list_resources()),
            "resourceTemplates": len(await mcp_client.list_resource_templates()),
            "prompts": len(await mcp_client.list_prompts()),
        }


def _inspector(env: dict[str, str], *options: str) -> dict[str, Any]:
    """Run one Inspector command against the server.

    Args:
        env: Environment variables for the server.
        *options: The Inspector options: --method and its arguments.

    Returns:
        The JSON answer Inspector prints.

    Raises:
        RuntimeError: If Inspector exits with an error, with what it printed.
    """
    pairs = [arg for key, value in env.items() for arg in ("-e", f"{key}={value}")]
    command = ["npx", "--yes", INSPECTOR, "--cli", "uv", "run", "avenir-mcp", *options, *pairs]
    done = subprocess.run(  # noqa: S603  # nosec B603 - fixed argument list
        command, capture_output=True, text=True, check=False, timeout=120
    )
    if done.returncode != 0:
        raise RuntimeError(f"{' '.join(options)}: exit {done.returncode}\n{done.stderr[-2000:]}")
    return json.loads(done.stdout)  # type: ignore[no-any-return]


def _checks() -> list[tuple[str, list[str], Callable[[dict[str, Any]], bool]]]:
    """List what to ask the server, and what the answer must satisfy.

    Returns:
        (name, Inspector options, check of the answer) triples.
    """
    budget = demo_budget.PLAN_ID
    count = asyncio.run(_in_process())
    return [
        ("tools, schemas portable", ["--method", "tools/list", "--strict"],
         lambda d: len(d["tools"]) == count["tools"]),
        ("resources", ["--method", "resources/list"],
         lambda d: len(d["resources"]) == count["resources"]),
        ("resource templates", ["--method", "resources/templates/list"],
         lambda d: len(d["resourceTemplates"]) == count["resourceTemplates"]),
        ("prompts", ["--method", "prompts/list"], lambda d: len(d["prompts"]) == count["prompts"]),
        ("list_plans on the demo budget",
         ["--method", "tools/call", "--tool-name", "list_plans"],
         lambda d: not d.get("isError") and d["structuredContent"]["result"][0]["id"] == budget),
        ("guide resource", ["--method", "resources/read", "--uri", "avenir-mcp://guide"],
         lambda d: "YNAB method" in d["contents"][0]["text"]),
        ("monthly_review prompt",
         ["--method", "prompts/get", "--prompt-name", "monthly_review",
          "--prompt-args", f"plan_id={budget}"],
         lambda d: "get_monthly_summary" in d["messages"][0]["content"]["text"]),
    ]  # fmt: skip


def main() -> int:
    """Run every check and print one line each.

    Returns:
        0 when every check passes, 1 otherwise.
    """
    server = fake_ynab.serve()
    failed = 0
    with tempfile.TemporaryDirectory() as work:
        env = {
            "YNAB_API_KEY": "demo",
            "AVENIR_MCP_YNAB_URL": f"http://127.0.0.1:{server.server_port}/v1",
            "AVENIR_MCP_WRITE": "1",
            "AVENIR_MCP_NO_UPDATE_CHECK": "1",
            "AVENIR_MCP_JOURNAL": os.path.join(work, "journal.jsonl"),
        }
        # A virtual environment outside the project (see the development page) goes along.
        if "UV_PROJECT_ENVIRONMENT" in os.environ:
            env["UV_PROJECT_ENVIRONMENT"] = os.environ["UV_PROJECT_ENVIRONMENT"]
        for name, options, check in _checks():
            try:
                passed = check(_inspector(env, *options))
                detail = ""
            except (RuntimeError, KeyError, IndexError, ValueError) as error:
                passed, detail = False, f": {error}"
            failed += not passed
            print(f"{'ok  ' if passed else 'FAIL'} {name}{detail}")
    server.shutdown()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
