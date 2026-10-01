# Contributing

Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md). How decisions
are made and who does what: [GOVERNANCE.md](GOVERNANCE.md). How the code is organised:
[ARCHITECTURE.md](ARCHITECTURE.md).

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

## Tests

Every change to the behaviour comes with automated tests in `tests/`, added in the same
pull request:

- **New functionality** — a tool, an argument, a resource, a prompt, a new case
  handled — comes with tests of what it does and of what it refuses.
- **A bug fix** comes with a regression test that fails without the fix.

The test is written first and seen to fail. Coverage of lines and branches stays at
100 %: `just check` fails otherwise. A pull request without tests for what it changes
is not merged. Documentation, CI and dependency updates are the exception.

## Coding standards

The code follows these guides, and the checks enforce them: `just check` and
`just hygiene` run them locally, and the required **CI passed** check runs them on every
pull request.

| Guide | Enforced by |
|---|---|
| [PEP 8](https://peps.python.org/pep-0008/), as `ruff format` writes it (lines of 100 characters at most) | `ruff format --check`, `pylint` (score 10.00) |
| [PEP 257](https://peps.python.org/pep-0257/) docstrings in the [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings), complete: `Args:`, `Returns:`, `Raises:` | `ruff check` (rules `D` and `DOC`), `pydoclint` |
| Type annotations everywhere, checked strictly | `mypy --strict` |
| Sorted imports; no risky pattern (bandit's rules) | `ruff check` (rules `I` and `S`) |
| One word per idea in the code's vocabulary | `lexdrift check` |
| Spelling in code and documentation | `typos` |
| Copyright and licence stated for every file, as [SPDX](https://spdx.dev) tags ([REUSE](https://reuse.software)) | `reuse lint` |

A new file starts with the project's two SPDX lines, after a shebang if it has one and
before a module's docstring:

```python
# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT
```

This command writes them, with the current year:

```bash
uvx --from 'reuse[charset-normalizer]==6.2.0' reuse annotate --template avenir \
  --copyright "The avenir-mcp contributors" --license MIT FILE
```

A file that cannot hold a comment (Markdown, JSON, an image, a lock file) is
covered by `REUSE.toml` instead.

[AGENTS.md](AGENTS.md) adds the rules specific to this project: secrets, untrusted text,
tool descriptions written for an agent, pydantic models for structured data.

## Documentation

The site lives in `docs/`: [Starlight](https://starlight.astro.build), in English,
French, Spanish, German and Dutch. The tool reference, the security page and every JSON example are
generated: run `uv run python -m docsgen` after changing a tool, then `just docs` (a
broken internal link in any language fails the build) or `just docs-serve` to read the
result. Examples come from the invented demo budget in `evals/demo_budget.py`, never
from a real one.

A page written by hand exists in every language: a test fails when an English
page has no counterpart in a translation. Change them all together. Generated pages
stay in English, and the other languages show them with a "not translated" notice.

The site is published on GitHub Pages and on Cloudflare Pages, which builds it with
`npm run build:cloudflare` and sends the security headers of `docs/cloudflare/_headers`
(Content-Security-Policy, HSTS, `nosniff`, `X-Frame-Options`). The build computes the
hash of every inline script and style for the policy, so a new one needs no change, and
fails when a required header is missing or weakened.

## Proposing a feature

Open a [feature request](https://github.com/mathbeal/avenir-mcp/issues/new?template=feature_request.yml):
describe the task and what you would say to the agent, not the tool you imagine. The
[documentation](https://mathbeal.github.io/avenir-mcp/project/propose-a-feature/) says what makes
a proposal easy to accept.

## Reporting a bad suggestion or a confusing tool

The most useful report shows what the agent asked, which tool it called with which
arguments, and what it should have done instead. Anonymise the amounts and payees.

## Developer Certificate of Origin

Every commit of a pull request is signed off: `git commit -s` adds the line
`Signed-off-by: Your Name <you@example.org>`. It certifies the
[Developer Certificate of Origin](https://developercertificate.org): you wrote the change,
or have the right to submit it under the project's MIT licence.

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
