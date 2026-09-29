"""Every operation of YNAB's API is used by a tool, planned, or left out with a reason."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from docsgen import api, errors


def test_every_operation_is_used_or_classified_once() -> None:
    """An operation YNAB adds, or one a tool stops using, has to be classified."""
    operations = {op["id"] for op in api.snapshot()["operations"]}
    used, _ = api.used()
    classified = set(api.coverage())
    assert operations == set(used) | classified
    assert not set(used) & classified, "an operation both used and classified"


def test_a_left_out_operation_says_why() -> None:
    """Every planned or excluded operation carries its status and a reason."""
    for entry in api.coverage().values():
        assert entry["status"] in ("planned", "excluded")
        assert entry["reason"].strip()


def test_every_client_call_is_an_operation_of_the_api() -> None:
    """The client calls only paths YNAB documents: an undocumented one may disappear."""
    _, unknown = api.used()
    assert not unknown


def test_an_undocumented_path_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    """The old /budgets paths would be reported, not silently accepted."""
    monkeypatch.setattr(api, "client_calls", lambda: {"old": {("GET", "/budgets/{}/accounts")}})
    _, unknown = api.used()
    assert unknown == ["GET /budgets/{}/accounts in client.old"]


def test_every_tool_and_resource_reaches_the_api() -> None:
    """A tool that uses no operation would be a sign the analysis lost it."""
    used, _ = api.used()
    users = {label for labels in used.values() for label in labels}
    assert set(errors.reached()) - users == {"avenir-mcp://guide"}


def test_operations_are_read_from_the_specification() -> None:
    """Id, method and path of each operation, sorted, with the specification's version."""
    spec: dict[str, Any] = {
        "info": {"version": "9.9.9"},
        "paths": {
            "/plans/{plan_id}": {"get": {"operationId": "getPlan"}, "parameters": []},
            "/plans": {"post": {"operationId": "createPlan"}, "get": {"operationId": "getPlans"}},
        },
    }
    assert api.operations(spec) == {
        "version": "9.9.9",
        "operations": [
            {"id": "getPlans", "method": "GET", "path": "/plans"},
            {"id": "createPlan", "method": "POST", "path": "/plans"},
            {"id": "getPlan", "method": "GET", "path": "/plans/{plan_id}"},
        ],
    }


def _ops(*ops: tuple[str, str, str]) -> dict[str, Any]:
    return {"version": "1", "operations": [{"id": i, "method": m, "path": p} for i, m, p in ops]}


def test_differences_name_what_was_added_removed_or_moved() -> None:
    """Each change of YNAB's API is one line a maintainer can act on."""
    old = _ops(("a", "GET", "/a"), ("b", "GET", "/b"), ("c", "GET", "/c"))
    new = _ops(("a", "GET", "/a"), ("c", "GET", "/plans/c"), ("d", "POST", "/d"))
    assert api.differences(old, new) == [
        "added: POST /d (d)",
        "changed: c GET /c -> GET /plans/c",
        "removed: GET /b (b)",
    ]
    assert not api.differences(old, old)


def test_the_check_passes_fails_and_updates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unchanged: 0. Changed: 1 and what to do. --update: the snapshot is rewritten."""
    snapshot = tmp_path / "ynab-operations.json"
    snapshot.write_text(json.dumps(_ops(("a", "GET", "/a"))), encoding="utf-8")
    monkeypatch.setattr(api, "SNAPSHOT", snapshot)
    monkeypatch.setattr(api, "_live", lambda: _ops(("a", "GET", "/a")))
    assert api.main([]) == 0
    monkeypatch.setattr(api, "_live", lambda: _ops(("a", "GET", "/plans/a")))
    assert api.main([]) == 1
    assert "--update" in capsys.readouterr().out
    assert api.main(["--update"]) == 0
    assert json.loads(snapshot.read_text(encoding="utf-8"))["operations"][0]["path"] == "/plans/a"


def _tool_rows() -> dict[str, tuple[str, str]]:
    """The page's per-tool table: each tool or resource with what it reads and writes."""
    page = api.page()
    table = page[page.index("| Tool or resource | Reads | Writes |") :]
    rows = {}
    for line in table.splitlines()[2:]:
        if not line.startswith("| `"):
            break
        label, reads, writes = (cell.strip() for cell in line.strip("|").split(" | "))
        rows[label.strip("`")] = (reads, writes)
    return rows


def test_the_page_lists_every_tool_and_resource_once_with_its_operations() -> None:
    """One row per tool or resource, as found by following the code."""
    used, _ = api.used()
    assert set(_tool_rows()) == {label for labels in used.values() for label in labels}


def test_a_tool_reads_with_get_and_writes_with_the_other_methods() -> None:
    """apply_categories reads transactions and writes them; list_plans only reads."""
    rows = _tool_rows()
    reads, writes = rows["apply_categories"]
    assert "`GET /transactions`" in reads
    assert writes == "`PATCH /transactions`"
    assert rows["list_plans"] == ("`GET /plans`", "—")
