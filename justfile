# Run `just` to see the recipes.
default:
    @just --list

# Install the project and its development tools.
setup:
    uv sync

# Every gate CI runs, in the same order.
check: lint types test vocabulary lock

lint:
    uv run black --check avenir_mcp tests evals docsgen
    uv run isort --check avenir_mcp tests evals docsgen
    uv run pylint avenir_mcp tests evals docsgen
    uv run ruff check avenir_mcp
    uv run deptry .

types:
    uv run mypy

test:
    uv run pytest

# One word per idea, against the accepted baseline.
vocabulary:
    uvx lexdrift check avenir_mcp --baseline lexdrift.lock

lock:
    uv lock --check

# Reformat.
fix:
    uv run isort avenir_mcp tests evals docsgen
    uv run black avenir_mcp tests evals docsgen

# Audit the workflows and hunt typos, as CI does.
hygiene:
    uvx typos .
    uvx zizmor --persona=regular .github/workflows/

# Known vulnerabilities in the locked dependencies.
audit:
    uv export --frozen --no-emit-project --all-groups -o /tmp/avenir-req.txt
    uvx pip-audit --strict --disable-pip -r /tmp/avenir-req.txt

# Build the wheel and the sdist, and check them.
build:
    rm -rf dist
    uv build
    uv run --no-project --with twine twine check --strict dist/*

# Regenerate CHANGELOG.md from the commit history.
changelog:
    uvx git-cliff -o CHANGELOG.md

# Fail if CHANGELOG.md is not what the history produces.
changelog-check:
    uvx git-cliff -o /tmp/avenir-cliff.md
    diff -u CHANGELOG.md /tmp/avenir-cliff.md

# The server as a client sees it, through the official MCP Inspector (needs Node.js).
inspect:
    uv run python -m evals.inspector

# A real agent on the demo budget (uses your Claude plan; about 1 USD).
evaluate:
    uv run python -m evals.run

# Regenerate the tool reference and the examples, then build the site (EN, FR, ES).
docs:
    uv run python -m docsgen
    npm --prefix docs ci
    npm --prefix docs test
    npm --prefix docs run build

# Serve the documentation locally with live reload.
docs-serve:
    npm --prefix docs run dev
