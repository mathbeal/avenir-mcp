# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Every rule YNAB states on what avenir-mcp sends is tested, does not apply, or is a gap."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from docsgen import api

ROOT = Path(__file__).resolve().parent.parent


def _entries() -> dict[str, dict[str, Any]]:
    """The entries of api/constraints.toml, by rule."""
    return {entry["rule"]: entry for entry in api.constraints()}


def test_every_rule_of_a_used_operation_has_one_entry() -> None:
    """A rule YNAB adds to a body avenir-mcp sends must be read and classified."""
    rules = [entry["rule"] for entry in api.constraints()]
    assert len(rules) == len(set(rules)), "a rule listed twice"
    missing = set(api.used_rules()) - set(rules)
    assert not missing, f"rules without an entry in api/constraints.toml: {sorted(missing)}"


def test_no_entry_names_a_rule_that_is_gone() -> None:
    """A rule YNAB removed or reworded leaves no stale entry behind."""
    stale = set(_entries()) - set(api.used_rules())
    assert not stale, f"entries for rules no longer in the specification: {sorted(stale)}"


def test_each_entry_has_its_status_and_what_backs_it() -> None:
    """Tested names its tests; not-applicable and gap say why."""
    for rule, entry in _entries().items():
        assert entry["status"] in ("tested", "not-applicable", "gap"), rule
        if entry["status"] == "tested":
            assert entry.get("tests"), rule
        else:
            assert entry.get("reason", "").strip(), rule


def _test_names(path: Path) -> set[str]:
    """The test functions a file defines."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def test_every_test_named_exists() -> None:
    """A renamed or deleted test cannot leave a rule looking covered."""
    for rule, entry in _entries().items():
        for name in entry.get("tests", []):
            file, _, function = name.partition("::")
            path = ROOT / file
            assert path.is_file(), f"{rule}: {file} does not exist"
            assert function in _test_names(path), f"{rule}: {name} does not exist"


def test_rules_are_read_from_field_descriptions_and_lengths() -> None:
    """A limiting sentence and a maxLength become rules; a plain description does not."""
    spec: dict[str, Any] = {
        "info": {"version": "1"},
        "paths": {
            "/things": {
                "post": {
                    "operationId": "createThing",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PostThing"}
                            }
                        }
                    },
                },
                "get": {"operationId": "getThings"},
            }
        },
        "components": {
            "schemas": {
                "PostThing": {"properties": {"thing": {"$ref": "#/components/schemas/SaveThing"}}},
                "SaveThing": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Base"},
                        {
                            "properties": {
                                "name": {"description": "The name.", "maxLength": 50},
                                "when": {"description": "A date. Future dates are not permitted."},
                                "parts": {"items": {"$ref": "#/components/schemas/Base"}},
                            }
                        },
                    ]
                },
                "Base": {"properties": {"kind": {"description": "Cannot be changed."}}},
            }
        },
    }
    assert api.operations(spec)["operations"] == [
        {"id": "getThings", "method": "GET", "path": "/things"},
        {
            "id": "createThing",
            "method": "POST",
            "path": "/things",
            "rules": [
                "Base.kind: Cannot be changed.",
                "SaveThing.name: maxLength 50",
                "SaveThing.when: Future dates are not permitted.",
            ],
        },
    ]


def test_a_changed_rule_is_a_difference() -> None:
    """YNAB rewording a rule shows as one rule removed and one added."""
    old = {"operations": [{"id": "a", "method": "PATCH", "path": "/a", "rules": ["A.x: Old."]}]}
    new = {"operations": [{"id": "a", "method": "PATCH", "path": "/a", "rules": ["A.x: New."]}]}
    assert api.differences(old, new) == ["rule added: a A.x: New.", "rule removed: a A.x: Old."]
