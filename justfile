# Run `just` to see the recipes.
default:
    @just --list

# Install the project and its development tools.
setup:
    uv sync

# Every gate CI runs, in the same order.
check: lint types test vocabulary lock

lint:
    uv run ruff format --check avenir_mcp tests evals docsgen benchmarks
    uv run pylint avenir_mcp tests evals docsgen benchmarks
    uv run ruff check avenir_mcp tests evals docsgen benchmarks
    uvx pydoclint==0.10.1 avenir_mcp
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

# Time the computing functions on a five-year plan of about 9,000 transactions.
bench:
    uv run pytest benchmarks -o addopts="" -p no:cacheprovider --benchmark-only --benchmark-sort=name --benchmark-columns=min,median,mean,rounds

# Reformat.
fix:
    uv run ruff check --select I --fix avenir_mcp tests evals docsgen benchmarks
    uv run ruff format avenir_mcp tests evals docsgen benchmarks

# Look for secrets in every commit of every branch, as CI does (needs Docker).
# It mounts the repository that holds the history, so a worktree works too.
secrets:
    docker run --rm -v "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)"):/repo" zricethezav/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f git /repo --redact --log-opts=--all

# Check every link of the README and the hand-written documentation, as CI does
# (needs Docker). Links inside the site are checked when it builds (`just docs`).
links:
    docker run --rm -v "$PWD:/input" -w /input lycheeverse/lychee@sha256:eaff3e0a13603c9a701accfcc84f44158bb77bf36ecfa4622b626056c3463892 --config lychee.toml --no-progress README.md CONTRIBUTING.md SECURITY.md AGENTS.md "docs/src/content/docs/**/*.md" "docs/src/content/docs/**/*.mdx"

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

# Mutation testing: change the code on purpose and check a test notices (about 30 s).
mutate:
    uv run mutmut run --max-children 8
    uv run mutmut results

# Compare the snapshot of YNAB's API with the live specification (network).
api-drift:
    uv run python -m docsgen.api

# The server as a client sees it, through the official MCP Inspector (needs Node.js).
inspect:
    uv run python -m evals.inspector

# A real agent on the demo budget (uses your Claude plan; about 1 USD).
evaluate:
    uv run python -m evals.run

# Regenerate the tool reference and the examples, then build the site in every language.
docs:
    uv run python -m docsgen
    npm --prefix docs ci
    npm --prefix docs test
    npm --prefix docs run build

# Serve the documentation locally with live reload.
docs-serve:
    npm --prefix docs run dev
