"""Find, in the source, every error message each tool can return.

Starting from a tool's function, calls are followed through the package (bare
names, names imported from avenir_mcp modules, and `module.function` calls) and
every `raise ToolError(...)` or `raise ValueError(...)` with a literal message is
collected. Messages keep their placeholders, e.g. `{account_id}`.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "avenir_mcp"
_RAISED = {"ToolError", "ValueError"}
# The HTTP client's errors are YNAB's own; the catalogue lists them apart.
_SKIPPED_MODULES = {"client"}

Functions = dict[tuple[str, str], ast.FunctionDef | ast.AsyncFunctionDef]


def _modules() -> dict[str, ast.Module]:
    return {p.stem: ast.parse(p.read_text(encoding="utf-8")) for p in PACKAGE.glob("*.py")}


def _functions(modules: dict[str, ast.Module]) -> Functions:
    return {
        (module, node.name): node
        for module, tree in modules.items()
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _imports(tree: ast.Module) -> tuple[dict[str, str], dict[str, str]]:
    """(name -> module it comes from, alias -> package module) for avenir_mcp imports."""
    names: dict[str, str] = {}
    modules: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("avenir_mcp")
        ):
            if node.module == "avenir_mcp":
                for alias in node.names:
                    modules[alias.asname or alias.name] = alias.name
            else:
                for alias in node.names:
                    names[alias.asname or alias.name] = node.module.split(".")[-1]
    return names, modules


def _placeholder(node: ast.expr) -> str:
    """A readable name for an interpolated expression: item['date'] or item.date -> date."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Constant):
            return str(node.slice.value)
        return _placeholder(node.value).removesuffix("s")
    if isinstance(node, ast.Call) and node.args:
        return _placeholder(node.args[0])
    return ast.unparse(node)


def _constants() -> dict[str, object]:
    """Module-level UPPER_CASE constants of the package, to show their values."""
    found: dict[str, object] = {}
    for path in PACKAGE.glob("*.py"):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        found[target.id] = node.value.value
    return found


_CONSTANTS = _constants()


def render(node: ast.expr) -> str | None:
    """A message as its template, or None when it is not written in the source."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                inner = value.value
                if isinstance(inner, ast.Name) and inner.id in _CONSTANTS:
                    parts.append(str(_CONSTANTS[inner.id]))
                    continue
                placeholder = "{" + _placeholder(inner) + "}"
                parts.append(f"'{placeholder}'" if value.conversion == ord("r") else placeholder)
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = render(node.left), render(node.right)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.IfExp):
        return render(node.body)
    return None


def _raised(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    messages = []
    for node in ast.walk(function):
        if (
            isinstance(node, ast.Raise)
            and isinstance(node.exc, ast.Call)
            and isinstance(node.exc.func, ast.Name)
            and node.exc.func.id in _RAISED
            and node.exc.args
        ):
            message = render(node.exc.args[0])
            if message is not None and len(message) > 20:
                messages.append(message)
    return messages


def _callees(
    module: str, function: ast.FunctionDef | ast.AsyncFunctionDef, modules: dict[str, ast.Module]
) -> list[tuple[str, str]]:
    names, aliases = _imports(modules[module])
    found = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            found.append((names.get(node.func.id, module), node.func.id))
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            target = aliases.get(node.func.value.id)
            if target:
                found.append((target, node.func.attr))
    return found


def tool_errors() -> dict[str, list[str]]:
    """Tool name -> the messages it can return, in the order they are raised."""
    modules = _modules()
    functions = _functions(modules)
    result: dict[str, list[str]] = {}
    for (module, name), node in functions.items():
        decorated = any(
            isinstance(d, ast.Call) and ast.unparse(d.func) == "mcp.tool"
            for d in node.decorator_list
        )
        if not decorated:
            continue
        seen: set[tuple[str, str]] = set()
        pending = [(module, name)]
        messages: list[str] = []
        while pending:
            key = pending.pop(0)
            if key in seen or key not in functions or key[0] in _SKIPPED_MODULES:
                continue
            seen.add(key)
            messages += [m for m in _raised(functions[key]) if m not in messages]
            pending += _callees(key[0], functions[key], modules)
        result[name] = messages
    return result
