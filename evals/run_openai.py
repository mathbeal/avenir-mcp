"""Run the evaluation with any model behind an OpenAI-compatible API.

Usage: uv run python -m evals.run_openai --model MODEL [--task ID ...]

The same tasks, demo budget and server as evals.run, but the agent is a small
tool-calling loop written here instead of Claude Code, so that models of other
providers can be compared. The API defaults to Mammouth (https://mammouth.ai),
which serves many providers' models; AVENIR_EVAL_BASE_URL points elsewhere.

The key is read from AVENIR_EVAL_API_KEY, or from the file named by
AVENIR_EVAL_API_KEY_FILE (default ~/.config/mammouth/api_key), and is never
printed. Only the demo budget's invented data is sent to the API.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic import SecretStr

from evals import fake_ynab
from evals.run import _mcp_config, cli, scored
from evals.tasks import Task

BASE_URL = "https://api.mammouth.ai/v1"
KEY_FILE = Path.home() / ".config" / "mammouth" / "api_key"
MAX_TURNS = 25
# Seconds to wait before trying a busy model again.
RETRY_PAUSES = (5, 15, 30)


class OutOfBudget(SystemExit):
    """The API account has no budget left: every further request would be refused."""


def api_key() -> SecretStr:
    """Read the API key, masked from here on.

    Returns:
        The key, shown as a mask when printed or logged.

    Raises:
        SystemExit: If no key is configured, saying where to put it.
    """
    key = os.getenv("AVENIR_EVAL_API_KEY", "")
    path = Path(os.getenv("AVENIR_EVAL_API_KEY_FILE", str(KEY_FILE)))
    if not key and path.exists():
        key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise SystemExit(f"No API key: set AVENIR_EVAL_API_KEY or write it to {path}.")
    return SecretStr(key)


def openai_tools(tools: list[Any]) -> list[dict[str, Any]]:
    """Describe MCP tools as OpenAI function tools.

    Args:
        tools: The tools listed by the MCP server.

    Returns:
        One {"type": "function", ...} entry per tool, its schema unchanged.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in tools
    ]


def tool_text(result: Any) -> str:
    """Give the model what a tool returned, as Claude Code would: JSON, or the error.

    Args:
        result: The MCP tool result.

    Returns:
        The structured content as JSON when there is some, else the text blocks.
    """
    if result.structured_content is not None and not result.is_error:
        return json.dumps(result.structured_content, ensure_ascii=False)
    return "\n".join(getattr(block, "text", "") for block in result.content)


async def chat(
    http: httpx.AsyncClient, model: str, messages: list[dict[str, Any]], tools: list[Any]
) -> dict[str, Any]:
    """Ask the model for its next message.

    Args:
        http: The client holding the API's base URL and key.
        model: The model's name at the API.
        messages: The conversation so far.
        tools: The tools, as OpenAI function tools.

    Returns:
        The API's JSON answer.

    Raises:
        OutOfBudget: If the account's budget is spent, which no retry can fix.
        RuntimeError: If the API refuses the request, with its answer; a busy model
            (429) or a server error (5xx) is tried again first, after a pause.
    """
    for pause in (*RETRY_PAUSES, None):
        response = await http.post(
            "/chat/completions", json={"model": model, "messages": messages, "tools": tools}
        )
        if response.status_code < 400:
            return response.json()  # type: ignore[no-any-return]
        if response.status_code == 429 and "budget" in response.text.lower():
            raise OutOfBudget(
                "The API account has no budget left: nothing more can run until it is topped up."
            )
        if pause is None or response.status_code not in (429, 500, 502, 503, 504):
            break
        await asyncio.sleep(pause)
    raise RuntimeError(f"API {response.status_code}: {response.text[:500]}")


async def _run_tools(mcp: Client[Any], requested: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Call the tools the model asked for, in order.

    Args:
        mcp: The client connected to avenir-mcp.
        requested: The model's tool calls.

    Returns:
        One tool message per call, for the conversation.
    """
    answers = []
    for call in requested:
        try:
            arguments = json.loads(call["function"].get("arguments") or "{}")
            result = await mcp.call_tool(call["function"]["name"], arguments, raise_on_error=False)
            content = tool_text(result)
        except (json.JSONDecodeError, RuntimeError, ValueError) as error:
            content = f"Error: {error}"
        answers.append({"role": "tool", "tool_call_id": call["id"], "content": content})
    return answers


def _server(url: str, journal: Path) -> StdioTransport:
    """Start avenir-mcp as evals.run does: over stdio, on the demo budget.

    Args:
        url: The demo budget's URL.
        journal: A fresh journal file.

    Returns:
        The transport to the server.
    """
    server = _mcp_config(url, journal)["mcpServers"]["avenir-mcp"]
    return StdioTransport(server["command"], server["args"], env=server["env"])


def _api() -> httpx.AsyncClient:
    """Open the model API; the key goes into the Authorization header only.

    Returns:
        The client, with the API's base URL and key.
    """
    headers = {"Authorization": f"Bearer {api_key().get_secret_value()}"}
    base = os.getenv("AVENIR_EVAL_BASE_URL", BASE_URL)
    return httpx.AsyncClient(base_url=base, headers=headers, timeout=180)


async def _agent(task: Task, model: str, url: str, journal: Path) -> dict[str, Any]:
    """Let the model work on a task with avenir-mcp's tools until it answers.

    Args:
        task: The task to run.
        model: The model's name at the API.
        url: The demo budget's URL.
        journal: A fresh journal file.

    Returns:
        The final reply, the tool calls, the turns and the token counts.
    """
    outcome: dict[str, Any] = {"reply": "", "tool_calls": [], "turns": MAX_TURNS,
                               "input_tokens": 0, "output_tokens": 0}  # fmt: skip
    messages: list[dict[str, Any]] = [{"role": "user", "content": task.prompt}]
    async with Client(_server(url, journal)) as mcp, _api() as http:
        tools = openai_tools(await mcp.list_tools())
        for turn in range(1, MAX_TURNS + 1):
            answer = await chat(http, model, messages, tools)
            usage = answer.get("usage") or {}
            outcome["input_tokens"] += usage.get("prompt_tokens", 0)
            outcome["output_tokens"] += usage.get("completion_tokens", 0)
            message = answer["choices"][0]["message"]
            messages.append(message)
            requested = message.get("tool_calls") or []
            if not requested:
                return {**outcome, "reply": message.get("content") or "", "turns": turn}
            outcome["tool_calls"] += [call["function"]["name"] for call in requested]
            messages += await _run_tools(mcp, requested)
    return outcome


def run_task(task: Task, model: str) -> dict[str, Any]:
    """Run one task against a fresh demo budget and score it.

    Args:
        task: The task to run.
        model: The model's name at the API.

    Returns:
        The result, in the same shape as evals.run's.
    """
    fake_ynab.STATE = fake_ynab.DemoBudget()
    budget = fake_ynab.serve()
    started = time.monotonic()
    error = ""
    try:
        with tempfile.TemporaryDirectory() as work:
            url = f"http://127.0.0.1:{budget.server_port}/v1"
            outcome = asyncio.run(_agent(task, model, url, Path(work) / "journal.jsonl"))
    except (RuntimeError, httpx.HTTPError) as failure:
        outcome = {"reply": "", "tool_calls": [], "turns": 0, "input_tokens": 0, "output_tokens": 0}
        error = str(failure)
    finally:
        budget.shutdown()
        budget.server_close()
    reply = str(outcome.pop("reply"))
    seconds = round(time.monotonic() - started, 1)
    return scored(task, reply, **outcome, cost_usd=None, seconds=seconds, error=error)


if __name__ == "__main__":
    sys.exit(cli(run_task, __doc__, None))
