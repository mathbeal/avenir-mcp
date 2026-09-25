# Contributing

## Getting set up

```bash
git clone https://github.com/mathbeal/avenir-mcp
cd avenir-mcp
uv sync
```

The tests never call YNAB. To try the server against your own budget, put your
token in `.env` (ignored by git, see `.env.example`) and point an MCP client or the
[MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) at
`uv run avenir-mcp`.

## Proposing a pull request

The path, from the issue to the merge, is in the
[documentation](https://mathbeal.github.io/avenir-mcp/project/pull-requests/): fork, branch,
tests first, `just check`, then `gh pr create --fill` and the template's checklist.

## What gets merged

Read [AGENTS.md](AGENTS.md) first. It states the rules the code holds to.

The checks listed there must pass. Tests are written before the code: a pull
request whose tests were written afterwards is hard to tell apart from one whose
tests were written to pass.

**Never paste real transactions, balances, account names or tokens** into an issue,
a fixture or a log. Invent them.

## Documentation

The site lives in `docs/`: [Starlight](https://starlight.astro.build), in English,
French and Spanish. The tool reference, the security page and every JSON example are
generated: run `uv run python -m docsgen` after changing a tool, then `just docs` (a
broken internal link in any language fails the build) or `just docs-serve` to read the
result. Examples come from the invented demo budget in `evals/demo_budget.py`, never
from a real one.

A page written by hand exists in the three languages: a test fails when an English
page has no French or Spanish counterpart. Change the three together. Generated pages
stay in English, and the other languages show them with a "not translated" notice.

## Proposing a feature

Open a [feature request](https://github.com/mathbeal/avenir-mcp/issues/new?template=feature_request.yml):
describe the task and what you would say to the agent, not the tool you imagine. The
[documentation](https://mathbeal.github.io/avenir-mcp/project/propose-a-feature/) says what makes
a proposal easy to accept.

## Reporting a bad suggestion or a confusing tool

The most useful report shows what the agent asked, which tool it called with which
arguments, and what it should have done instead. Anonymise the amounts and payees.

## Commit messages

Prefix the first line with the kind of change. The changelog will be generated
from them:

```
feat: preview category changes before applying them
fix: report an invalid month instead of YNAB's 404
docs: document the HTTP transport
test: cover the empty-budget case
chore: bump fastmcp
```
