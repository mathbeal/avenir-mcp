"""YNAB's API against avenir-mcp: every operation classified, and YNAB's changes caught.

`api/ynab-operations.json` is a snapshot of the operations YNAB's OpenAPI
specification lists. The operations avenir-mcp uses are found by following the
code from each tool and resource to the HTTP client; `api/coverage.toml` says why
each other one is planned or left out. Tests check that every operation is one or
the other, and that the client calls only documented paths.

`python -m docsgen.api` compares the snapshot with the live specification and fails
when YNAB added, removed or renamed an operation; `--update` rewrites the snapshot.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import httpx

from docsgen import errors

ROOT = Path(__file__).resolve().parent.parent
CLIENT = ROOT / "avenir_mcp" / "client.py"
SNAPSHOT = ROOT / "api" / "ynab-operations.json"
COVERAGE = ROOT / "api" / "coverage.toml"
SPEC_URL = "https://api.ynab.com/papi/open_api_spec.yaml"
METHODS = ("get", "post", "put", "patch", "delete")
STATUSES = ("covered", "planned", "excluded")
# YNAB took the announcement down; the archived copy is the one that still answers.
ANNOUNCEMENT_URL = (
    "https://web.archive.org/web/20260112213044/https://www.ynab.com/blog/budget-tab-breakdown"
)


def operations(spec: dict[str, Any]) -> dict[str, Any]:
    """Keep what the coverage needs from an OpenAPI specification.

    Args:
        spec: The specification, parsed.

    Returns:
        Its version and its operations: id, method and path, sorted by path.
    """
    found = [
        {"id": op["operationId"], "method": method.upper(), "path": path}
        for path, item in spec["paths"].items()
        for method, op in item.items()
        if method in METHODS
    ]
    found.sort(key=lambda op: (op["path"], METHODS.index(op["method"].lower())))
    return {"version": spec["info"]["version"], "operations": found}


def snapshot() -> dict[str, Any]:
    """Read the snapshot of YNAB's operations kept in the repository.

    Returns:
        Its version and its operations.
    """
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def coverage() -> dict[str, dict[str, Any]]:
    """Read the operations avenir-mcp does not use, and why.

    Returns:
        Each planned or excluded operation id's entry: status and reason.
    """
    with COVERAGE.open("rb") as file:
        return tomllib.load(file)["operations"]  # type: ignore[no-any-return]


def _template(node: ast.expr) -> str | None:
    """Turn the path a client function passes into a template, ids as {}.

    Args:
        node: The first argument of a _get, _post, _patch or _delete call.

    Returns:
        The path, e.g. "/plans/{}/accounts", or None when it is not written literally.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(str(v.value) if isinstance(v, ast.Constant) else "{}" for v in node.values)
    return None


def client_calls() -> dict[str, set[tuple[str, str]]]:
    """Read which API paths each function of the HTTP client calls, and how.

    Returns:
        Each client function's name with its (method, path template) pairs.
    """
    calls: dict[str, set[tuple[str, str]]] = {}
    for node in ast.parse(CLIENT.read_text(encoding="utf-8")).body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for call in ast.walk(node):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id in {f"_{m}" for m in METHODS}
                and call.args
            ):
                path = _template(call.args[0])
                if path is not None:
                    calls.setdefault(node.name, set()).add((call.func.id[1:].upper(), path))
    return calls


def _shape(path: str) -> str:
    """Write a path with every id as {}, so that templates can be compared.

    Args:
        path: A path with named ids, such as "/plans/{plan_id}".

    Returns:
        The same path with anonymous ids.
    """
    return re.sub(r"\{[^}]*\}", "{}", path)


def used() -> tuple[dict[str, list[str]], list[str]]:
    """Work out which tools and resources use each operation, following the code.

    Returns:
        Each used operation id with the tools and resources behind it, and the client
        calls that match no operation of the snapshot.
    """
    by_shape = {(op["method"], _shape(op["path"])): op["id"] for op in snapshot()["operations"]}
    function_ops: dict[str, set[str]] = {}
    unknown = []
    for function, calls in client_calls().items():
        for method, path in calls:
            op = by_shape.get((method, _shape(path)))
            if op is None:
                unknown.append(f"{method} {path} in client.{function}")
            else:
                function_ops.setdefault(function, set()).add(op)
    users: dict[str, set[str]] = {}
    for label, reached in errors.reached().items():
        for module, function in reached:
            if module == "client":
                for op in function_ops.get(function, set()):
                    users.setdefault(op, set()).add(label)
    return {op: sorted(labels) for op, labels in users.items()}, sorted(unknown)


def differences(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """Say what changed between two lists of operations.

    Args:
        old: The snapshot.
        new: The live specification's operations.

    Returns:
        One line per operation added, removed or moved to another path; empty when
        nothing changed.
    """
    before = {op["id"]: op for op in old["operations"]}
    after = {op["id"]: op for op in new["operations"]}
    lines = [
        f"added: {after[i]['method']} {after[i]['path']} ({i})"
        for i in after.keys() - before.keys()
    ]
    lines += [
        f"removed: {before[i]['method']} {before[i]['path']} ({i})"
        for i in before.keys() - after.keys()
    ]
    lines += [
        f"changed: {i} {before[i]['method']} {before[i]['path']}"
        f" -> {after[i]['method']} {after[i]['path']}"
        for i in before.keys() & after.keys()
        if before[i] != after[i]
    ]
    return sorted(lines)


def _short(op: dict[str, Any]) -> str:
    """Name an operation by method and path, without the plan every path starts with.

    Args:
        op: An operation of the snapshot.

    Returns:
        E.g. "GET /transactions" for GET /plans/{plan_id}/transactions.
    """
    return f"{op['method']} {op['path'].removeprefix('/plans/{plan_id}') or '/'}"


def by_tool(users: dict[str, list[str]], ops: list[dict[str, Any]]) -> list[str]:
    """Write one table row per tool or resource: the operations it reads and writes.

    Args:
        users: Each used operation id with the tools and resources behind it.
        ops: The snapshot's operations.

    Returns:
        The rows, read-only tools first, then alphabetically.
    """
    labels = {label for used_by in users.values() for label in used_by}
    reads: dict[str, list[str]] = {label: [] for label in labels}
    writes: dict[str, list[str]] = {label: [] for label in labels}
    for op in ops:
        for label in users.get(op["id"], []):
            side = reads if op["method"] == "GET" else writes
            side[label].append(f"`{_short(op)}`")
    return [
        f"| `{label}` | {', '.join(reads[label]) or '—'} | {', '.join(writes[label]) or '—'} |"
        for label in sorted(labels, key=lambda label: (bool(writes[label]), label))
    ]


def page() -> str:
    """Write the documentation page listing every operation and what avenir-mcp does with it.

    Returns:
        The page, in Markdown.
    """
    classified = coverage()
    users, _ = used()
    ops = snapshot()
    counts = {status: 0 for status in STATUSES}
    rows = []
    for op in ops["operations"]:
        if op["id"] in users:
            status = "covered"
            detail = ", ".join(f"`{label}`" for label in users[op["id"]])
        else:
            status, detail = classified[op["id"]]["status"], classified[op["id"]]["reason"]
        counts[status] += 1
        rows.append(f"| `{op['method']} {op['path']}` | {status} | {detail} |")
    return (
        "---\n"
        "title: YNAB API coverage\n"
        "description: Every operation of YNAB's API, and whether avenir-mcp uses it, plans to,"
        " or leaves it out.\n"
        "---\n\n"
        ":::note[Generated]\n"
        "Generated by `python -m docsgen`: the tools and resources are found by following the"
        " code; `api/coverage.toml` says why the other operations are planned or left out. A"
        " test fails when an operation is not classified, and a weekly check fails when YNAB"
        " changes its API.\n"
        ":::\n\n"
        "Source: YNAB's [OpenAPI specification](" + SPEC_URL + "), documented at"
        " [api.ynab.com](https://api.ynab.com/). YNAB renamed budgets to plans"
        " ([announcement](" + ANNOUNCEMENT_URL + ")): the"
        " operations say plan.\n\n"
        f"YNAB's API {ops['version']} has {len(ops['operations'])} operations: "
        f"{counts['covered']} used by avenir-mcp, {counts['planned']} planned, "
        f"{counts['excluded']} left out on purpose.\n\n"
        "| Operation | Status | Tools and resources, or why |\n|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n## By tool\n\n"
        "What each tool and resource reads and writes, paths without the leading"
        " `/plans/{plan_id}`. A tool calls only what the case at hand needs: `undo_operation`"
        " the operations of the kind it undoes, `get_spending_trends` one month per month"
        " asked.\n\n"
        "| Tool or resource | Reads | Writes |\n|---|---|---|\n"
        + "\n".join(by_tool(users, ops["operations"]))
        + "\n"
    )


def _live() -> dict[str, Any]:
    """Fetch YNAB's specification as published today.

    Returns:
        Its version and its operations.
    """
    import yaml  # pylint: disable=import-outside-toplevel  # only this command needs it

    response = httpx.get(SPEC_URL, timeout=30, follow_redirects=True)
    response.raise_for_status()
    return operations(yaml.safe_load(response.text))


def main(argv: list[str] | None = None) -> int:
    """Compare the snapshot with YNAB's live specification, or update it.

    Args:
        argv: The command-line arguments; None for sys.argv.

    Returns:
        0 when nothing changed (or the snapshot was updated), 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="rewrite the snapshot")
    options = parser.parse_args(argv)
    live = _live()
    if options.update:
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(json.dumps(live, indent=1) + "\n", encoding="utf-8")
        print(
            f"Snapshot updated: YNAB API {live['version']}, {len(live['operations'])} operations."
        )
        return 0
    changes = differences(snapshot(), live)
    if not changes:
        print(f"YNAB API {live['version']}: no change since the snapshot.")
        return 0
    print(f"YNAB's API changed ({snapshot()['version']} -> {live['version']}):")
    print("\n".join(f"- {line}" for line in changes))
    print("Run `uv run python -m docsgen.api --update`, then classify them in api/coverage.toml.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
