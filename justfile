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

# A real agent on the demo budget (uses your Claude plan; about 1 USD).
evaluate:
    uv run python -m evals.run

# Build the documentation site, failing on any warning.
docs:
    uv run --group docs mkdocs build --strict

# Serve the documentation locally with live reload.
docs-serve:
    uv run --group docs mkdocs serve
