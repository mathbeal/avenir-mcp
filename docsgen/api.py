"""YNAB's API against avenir-mcp: every operation classified, and YNAB's changes caught.

`api/ynab-operations.json` is a snapshot of the operations YNAB's OpenAPI
specification lists. The operations avenir-mcp uses are found by following the
code from each tool and resource to the HTTP client; `api/coverage.toml` says why
each other one is planned or left out. Tests check that every operation is one or
the other, and that the client calls only documented paths.

The snapshot also keeps, for each operation that takes a body, the rules the
specification states on what it takes: each sentence of a field's description that
limits it ("not supported", "cannot", "will be ignored"…) and each maximum length.
`api/constraints.toml` says, for every rule of an operation avenir-mcp uses, which
test covers it, why it does not apply, or that it is a known gap. A rule YNAB adds
or rewords is caught by the same weekly check.

`python -m docsgen.api` compares the snapshot with the live specification and fails
when YNAB added, removed or renamed an operation, or changed one of its rules;
`--update` rewrites the snapshot.
"""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import httpx

from docsgen import errors, snapshots

ROOT = Path(__file__).resolve().parent.parent
CLIENT = ROOT / "avenir_mcp" / "client.py"
SNAPSHOT = ROOT / "api" / "ynab-operations.json"
COVERAGE = ROOT / "api" / "coverage.toml"
CONSTRAINTS = ROOT / "api" / "constraints.toml"
SPEC_URL = "https://api.ynab.com/papi/open_api_spec.yaml"
METHODS = ("get", "post", "put", "patch", "delete")
STATUSES = ("covered", "planned", "excluded")
# YNAB took the announcement down; the archived copy is the one that still answers.
ANNOUNCEMENT_URL = (
    "https://web.archive.org/web/20260112213044/https://www.ynab.com/blog/budget-tab-breakdown"
)


# Words by which a field's description limits what YNAB takes. A sentence that only
# describes the field is caught too at times: constraints.toml says so.
_RULE = re.compile(
    r"not supported|cannot|may not|must|requires|will be ignored|not permitted|not allowed"
    r"|return an error|default",
    re.IGNORECASE,
)


def _ref(node: dict[str, Any]) -> str | None:
    """Name the schema a node points to, if it does.

    Args:
        node: A part of the specification.

    Returns:
        The schema's name, or None.
    """
    ref = node.get("$ref")
    return str(ref).rsplit("/", 1)[-1] if ref else None


def _field_rules(name: str, field: str, prop: dict[str, Any]) -> list[str]:
    """The rules a field's description and keywords state.

    Args:
        name: The schema's name.
        field: The field's name.
        prop: The field's definition.

    Returns:
        One line per rule, e.g. "SaveCategory.goal_frequency: Requires goal_target.".
    """
    text = " ".join(str(prop.get("description") or "").split())
    rules = [s for s in re.split(r"(?<=\.)\s+", text) if _RULE.search(s)]
    if "maxLength" in prop:
        rules.append(f"maxLength {prop['maxLength']}")
    return [f"{name}.{field}: {rule}" for rule in rules]


def _rules(schemas: dict[str, Any], name: str, seen: set[str]) -> list[str]:
    """Collect the rules of a schema and of every schema it contains.

    Args:
        schemas: The specification's schemas.
        name: The schema to start from.
        seen: Schemas already visited, so that each is read once.

    Returns:
        The rules, one line each.
    """
    if name in seen:
        return []
    seen.add(name)
    schema = schemas[name]
    found: list[str] = []
    for part in schema.get("allOf", [schema]):
        if inner := _ref(part):
            found += _rules(schemas, inner, seen)
            continue
        for field, prop in part.get("properties", {}).items():
            found += _field_rules(name, field, prop)
            nested = [prop, prop.get("items", {}), *prop.get("allOf", []), *prop.get("oneOf", [])]
            for node in nested:
                if inner := _ref(node):
                    found += _rules(schemas, inner, seen)
    return found


def _body_rules(spec: dict[str, Any], op: dict[str, Any]) -> list[str]:
    """The rules on the body an operation takes.

    Args:
        spec: The specification, parsed.
        op: One of its operations.

    Returns:
        The rules, sorted; empty for an operation without a body.
    """
    body = op.get("requestBody", {}).get("content", {}).get("application/json", {})
    name = _ref(body.get("schema", {}))
    return sorted(set(_rules(spec["components"]["schemas"], name, set()))) if name else []


def operations(spec: dict[str, Any]) -> dict[str, Any]:
    """Keep what the coverage needs from an OpenAPI specification.

    Args:
        spec: The specification, parsed.

    Returns:
        Its version and its operations: id, method and path, sorted by path, and the
        rules on the body of those that take one.
    """
    found = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method in METHODS:
                entry = {"id": op["operationId"], "method": method.upper(), "path": path}
                if rules := _body_rules(spec, op):
                    entry["rules"] = rules
                found.append(entry)
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


def constraints() -> list[dict[str, Any]]:
    """Read what avenir-mcp does with each rule of the operations it uses.

    Returns:
        One entry per rule: the rule, its status (tested, not-applicable or gap), and
        the tests that cover it or the reason.
    """
    with CONSTRAINTS.open("rb") as file:
        return tomllib.load(file)["rule"]  # type: ignore[no-any-return]


def used_rules() -> dict[str, list[str]]:
    """The rules of the operations avenir-mcp uses, each with those operations.

    Returns:
        Each rule with the ids of the used operations whose body it limits.
    """
    users, _ = used()
    rules: dict[str, list[str]] = {}
    for op in snapshot()["operations"]:
        if op["id"] in users:
            for rule in op.get("rules", []):
                rules.setdefault(rule, []).append(op["id"])
    return rules


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
        One line per operation added, removed or moved to another path, and per rule
        added or removed; empty when
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
    both = before.keys() & after.keys()
    lines += [
        f"changed: {i} {before[i]['method']} {before[i]['path']}"
        f" -> {after[i]['method']} {after[i]['path']}"
        for i in both
        if (before[i]["method"], before[i]["path"]) != (after[i]["method"], after[i]["path"])
    ]
    for i in both:
        old_rules, new_rules = set(before[i].get("rules", [])), set(after[i].get("rules", []))
        lines += [f"rule added: {i} {rule}" for rule in new_rules - old_rules]
        lines += [f"rule removed: {i} {rule}" for rule in old_rules - new_rules]
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
    update = snapshots.update_requested(argv, __doc__)
    live = _live()
    if update:
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
    print(
        "Run `uv run python -m docsgen.api --update`, then classify them in api/coverage.toml"
        " and api/constraints.toml."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
