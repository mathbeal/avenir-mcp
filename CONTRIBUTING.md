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

## Code review

A pull request is reviewed on GitHub, in public: comments go on the lines they are
about, and the author answers with new commits on the same branch. A review says what
is wrong and why, and points to the rule it relies on (this file, [AGENTS.md](AGENTS.md),
[SECURITY.md](SECURITY.md)); a question is fine, a demand without a reason is not.

### What the reviewer checks

The checks of CI cover what a machine can see: formatting, lint, types, coverage,
vocabulary, spelling, the workflows, known vulnerabilities, secrets. The reviewer reads
for what they cannot:

- **Behaviour.** The change does what the title and the description say, and nothing
  else. Errors say what to fix. A tool's description, which the agent reads, matches
  what the tool does.
- **Tests.** New behaviour has tests of what it does and of what it refuses; a fix has
  a regression test that fails without it. The tests check the behaviour, not the
  implementation, and use invented data only.
- **Security.** The change keeps every claim of the
  [assurance case](SECURITY.md#assurance-case) true, or updates it in the same pull
  request. In particular: a tool that changes a plan carries the `write` tag and the
  matching annotations, and goes through `confirm.py` with a preview and, where YNAB
  allows it, an undo (the exceptions are named in [SECURITY.md](SECURITY.md#scope)); payee
  names and memos pass through `text.untrusted` before they reach a question or an
  answer; a secret stays a `SecretStr`; the journal and the logs hold no payee, memo
  or transaction amount; no new network destination, file or environment variable
  appears without being documented; a new dependency comes with its reason; a
  workflow keeps its actions pinned by commit and its permissions minimal.
- **YNAB's API terms.** Requests stay within the hourly limit and go through
  `client.py`; an operation newly used is removed from `api/coverage.toml`, and each
  rule YNAB states on what it sends has its test in `api/constraints.toml`; YNAB's
  name, attribution and image are used as the terms allow.
- **Documentation.** If a tool, its arguments or its answers changed, the generated
  pages were regenerated (`uv run python -m docsgen`). A page written by hand was
  changed in all five languages of the site: English, French, Spanish, German and
  Dutch. A new environment variable is documented.
- **Title.** The pull request is squashed and its title becomes the commit message the
  changelog is generated from: it starts with the kind of change (`feat:`, `fix:`,
  …), says what changes for a user, and a change that breaks a configuration or a
  tool's interface is marked with `!` (`feat!: …`).

### What is required to merge

- **CI passed** and **MCP Inspector** are green, every commit is signed off, and the
  title passes its check.
- Every comment is answered: resolved by a commit, or settled in the discussion.
- **An approving review by someone other than the author.** A pull request from a
  contributor is approved by the maintainer. With two maintainers or more, a pull
  request written by a maintainer is approved by another maintainer, or by a
  [reviewer](GOVERNANCE.md#roles) whose review that maintainer accepts, before it is
  merged.

Today the project has a single maintainer (see [GOVERNANCE.md](GOVERNANCE.md)), so
nobody else reviews the maintainer's own changes. Until a second maintainer exists,
the maintainer goes through the checklist above for each of them before merging it,
the same checks run again on `main` once it is merged, and anyone can comment on a
pull request or a commit after the fact.

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
