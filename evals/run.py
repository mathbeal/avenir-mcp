"""Run the evaluation: a real Claude agent, Avenir, and the demo budget.

Usage: uv run python -m evals.run [--model sonnet] [--task ID ...]

Each task gets a fresh demo budget, a fresh journal and an empty working
directory, so no memory or project file from this machine leaks in. Only
Avenir's tools are allowed. Results go to evals/results/.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # noqa: S404  # nosec B404 - runs the local `claude` CLI
import sys
import tempfile
import time
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
    return {"mcpServers": {"avenir": {"command": "uv", "args": args, "env": env}}}


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
                calls.append(str(block.get("name", "")).removeprefix("mcp__avenir__"))
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
                [
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
                    "mcp__avenir",
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
    text = str(final.get("result", ""))
    answer_ok, state_ok = task.answer(text), task.state(fake_ynab.STATE)
    usage = final.get("usage", {})
    return {
        "task": task.task_id,
        "tags": task.tags,
        "passed": answer_ok and state_ok,
        "answer_ok": answer_ok,
        "state_ok": state_ok,
        "tool_calls": _tool_calls(events),
        "turns": final.get("num_turns"),
        "input_tokens": usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cost_usd": final.get("total_cost_usd"),
        "seconds": seconds,
        "reply": text[-600:],
        "exit_code": done.returncode,
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


def main() -> int:
    """Run the selected tasks and write the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--task", action="append", help="task id; repeat to run several")
    options = parser.parse_args()
    tasks = [t for t in TASKS if not options.task or t.task_id in options.task]
    results = []
    for task in tasks:
        result = run_task(task, options.model)
        results.append(result)
        print(f"{task.task_id}: {'pass' if result['passed'] else 'FAIL'}", file=sys.stderr)
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (RESULTS / f"{stamp}-{options.model}.json").write_text(json.dumps(results, indent=1))
    report = _report(results, options.model)
    (RESULTS / f"{stamp}-{options.model}.md").write_text(report)
    print(report)
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
