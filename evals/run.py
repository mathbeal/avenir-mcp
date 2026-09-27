"""Run the evaluation: a real Claude agent, avenir-mcp, and the demo budget.

Usage: uv run python -m evals.run [--model sonnet] [--task ID ...]

Each task gets a fresh demo budget, a fresh journal and an empty working
directory, so no memory or project file from this machine leaks in. Only
avenir-mcp's tools are allowed. Results go to evals/results/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # noqa: S404  # nosec B404 - runs the local `claude` CLI
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from evals import fake_ynab
from evals.tasks import TASKS, Task

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evals" / "results"


def _mcp_config(url: str, journal: Path) -> dict[str, Any]:
    env = {
        "YNAB_API_KEY": "demo",
        "AVENIR_MCP_YNAB_URL": url,
        "AVENIR_MCP_WRITE": "1",
        "AVENIR_MCP_JOURNAL": str(journal),
        "PATH": os.environ["PATH"],
    }
    if "UV_PROJECT_ENVIRONMENT" in os.environ:
        env["UV_PROJECT_ENVIRONMENT"] = os.environ["UV_PROJECT_ENVIRONMENT"]
    args = ["run", "--quiet", "--no-dev", "--directory", str(ROOT), "avenir-mcp"]
    return {"mcpServers": {"avenir-mcp": {"command": "uv", "args": args, "env": env}}}


def _events(stdout: str) -> list[dict[str, Any]]:
    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _tool_calls(events: list[dict[str, Any]]) -> list[str]:
    calls = []
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                calls.append(str(block.get("name", "")).removeprefix("mcp__avenir-mcp__"))
    return calls


def run_task(task: Task, model: str) -> dict[str, Any]:
    """Run one task against a fresh demo budget and score it."""
    fake_ynab.STATE = fake_ynab.DemoBudget()
    server = fake_ynab.serve()
    try:
        with tempfile.TemporaryDirectory() as work:
            config = Path(work) / "mcp.json"
            url = f"http://127.0.0.1:{server.server_port}/v1"
            config.write_text(json.dumps(_mcp_config(url, Path(work) / "journal.jsonl")))
            started = time.monotonic()
            done = subprocess.run(  # noqa: S603  # nosec B603 - fixed argument list
                [  # noqa: S607 - the user's own claude CLI, found on PATH
                    "claude",
                    "-p",
                    task.prompt,
                    "--model",
                    model,
                    "--output-format",
                    "stream-json",
                    "--verbose",
                    "--mcp-config",
                    str(config),
                    "--strict-mcp-config",
                    "--allowedTools",
                    "mcp__avenir-mcp",
                    "--permission-mode",
                    "dontAsk",
                    "--no-session-persistence",
                ],
                cwd=work,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
            seconds = round(time.monotonic() - started, 1)
    finally:
        server.shutdown()
        server.server_close()
    events = _events(done.stdout)
    final = next((e for e in reversed(events) if e.get("type") == "result"), {})
    usage = final.get("usage", {})
    return scored(
        task,
        str(final.get("result", "")),
        tool_calls=_tool_calls(events),
        turns=final.get("num_turns"),
        input_tokens=usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cost_usd=final.get("total_cost_usd"),
        seconds=seconds,
        exit_code=done.returncode,
    )


def scored(task: Task, reply: str, **measures: Any) -> dict[str, Any]:
    """Score the agent's reply and the demo budget's state after a task.

    Args:
        task: The task that ran.
        reply: The agent's final reply.
        **measures: What the runner measured: tool calls, turns, tokens, time.

    Returns:
        The task's result, as written to evals/results.
    """
    answer_ok, state_ok = task.answer(reply), task.state(fake_ynab.STATE)
    return {
        "task": task.task_id,
        "tags": task.tags,
        "passed": answer_ok and state_ok,
        "answer_ok": answer_ok,
        "state_ok": state_ok,
        **measures,
        "reply": reply[-600:],
    }


def _report(results: list[dict[str, Any]], model: str) -> str:
    passed = sum(r["passed"] for r in results)
    lines = [
        f"# Evaluation — {model}",
        "",
        f"**{passed}/{len(results)} tasks passed.**",
        "",
        "| Task | Result | Answer | Budget state | Tool calls | Seconds |",
        "|---|---|---|---|---|---:|",
    ]
    for r in results:
        calls = ", ".join(r["tool_calls"]) or "none"
        lines.append(
            f"| {r['task']} | {'pass' if r['passed'] else 'FAIL'} | "
            f"{'ok' if r['answer_ok'] else 'wrong'} | {'ok' if r['state_ok'] else 'wrong'} | "
            f"{calls} | {r['seconds']} |"
        )
    return "\n".join(lines) + "\n"


def evaluate(runner: Callable[[Task, str], dict[str, Any]], model: str, ids: list[str]) -> int:
    """Run the selected tasks with a runner, then write and print the report.

    Args:
        runner: Runs one task with a model and returns its scored result.
        model: The model's name, as the runner knows it.
        ids: The tasks to run; all of them when empty.

    Returns:
        0 when every task passed, 1 otherwise.
    """
    results = []
    for task in [t for t in TASKS if not ids or t.task_id in ids]:
        result = runner(task, model)
        results.append(result)
        status = "pass" if result["passed"] else "FAIL"
        print(f"{task.task_id}: {status} {result.get('error', '')[:200]}".rstrip(), file=sys.stderr)
    RESULTS.mkdir(parents=True, exist_ok=True)
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-{re.sub(r'[^A-Za-z0-9._-]+', '_', model)}"
    (RESULTS / f"{name}.json").write_text(json.dumps(results, indent=1))
    report = _report(results, model)
    (RESULTS / f"{name}.md").write_text(report)
    print(report)
    return 0 if all(r["passed"] for r in results) else 1


def cli(runner: Callable[[Task, str], dict[str, Any]], doc: str | None, model: str | None) -> int:
    """Read the command line, then run the evaluation.

    Args:
        runner: Runs one task with a model and returns its scored result.
        doc: The command's help text.
        model: The default model; None to require --model.

    Returns:
        0 when every task passed, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=doc)
    parser.add_argument("--model", default=model, required=model is None, help="model name")
    parser.add_argument("--task", action="append", help="task id; repeat to run several")
    options = parser.parse_args()
    return evaluate(runner, options.model, options.task or [])


if __name__ == "__main__":
    sys.exit(cli(run_task, __doc__, "sonnet"))
