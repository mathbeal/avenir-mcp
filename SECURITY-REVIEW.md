# Security review of avenir-mcp 0.3.0

| | |
|---|---|
| Date | 2026-10-01 |
| Version reviewed | 0.3.0 (tag `v0.3.0`, commit `426763d`); the package's code on `main` was the same that day |
| Reviewer | the maintainer, Mathieu Beal, assisted by an AI coding agent (Claude) that read the code paths and ran the tools listed below |
| Reference | the [assurance case](SECURITY.md#assurance-case) of `SECURITY.md` |

This is the project's security review: what was looked at, how, what was found, and
what risk remains. It is written for users deciding whether to trust avenir-mcp with
their YNAB token, and for contributors. A new review is due after a change to a trust
boundary, and at least once a year.

The reviewer is also the author of most of the code: this review is not independent.
Read it as a structured self-assessment, with the evidence named so that anyone can
check it.

## Scope

In scope: the Python package `avenir_mcp` as released in 0.3.0, its runtime
dependencies as locked in `uv.lock`, and the repository's GitHub workflows that test,
build and publish it.

Out of scope, as in the assurance case: an attacker who already controls the user's
account or machine, the MCP client and the model provider themselves, YNAB's service,
and running avenir-mcp as a shared server. The documentation site, the evaluations
(`evals/`) and the documentation generator (`docsgen/`) were read only where they touch
the release.

## Method

1. **Threat model.** The threats, trust boundaries and protected assets of the
   assurance case were taken as the starting point, and each claim of `SECURITY.md`
   was traced to the code that enforces it and the test that checks it.
2. **Code reading, by trust boundary.** Every path from an untrusted source to a
   sensitive action was read in full:

   | Boundary | Code read |
   |---|---|
   | agent → tools | `app.py` (write gate), `model.py`, `amounts.py`, `text.py`, the argument models and checks of every `tools_*.py` module |
   | agent → a write | `confirm.py`, `writes.py`, the confirmation question of every write tool, `tools_undo.py` |
   | server → YNAB | `client.py`: base URL, path segments, token, timeouts, rate limit, error messages |
   | local network and programs → HTTP transport | `server.py`, `http_auth.py`, FastMCP 4.0.9's `HostOriginGuardMiddleware` |
   | server → disk | `journal.py`, the update check's cache, the token file |
   | PyPI → agent | `updates.py` |
   | server → logs | `logs.py`, the log calls of the package, FastMCP's logging of tool errors |
   | repository → PyPI | `.github/workflows/*.yml`, `pyproject.toml`, `renovate.json` |

3. **Tools.** On 2026-10-01: `pip-audit --strict` on the locked runtime dependencies
   (74 packages) and on all dependency groups: no known vulnerability. `npm audit` on
   the documentation site's production dependencies: none. `zizmor` on the workflows:
   no finding with the persona CI uses; the `auditor` persona adds twelve notes, none
   exploitable (missing job-level concurrency limits, permissions without a comment,
   and a template expansion of a matrix value the workflow itself defines). The test
   suite (713 tests, 100 % of lines and branches), mypy in strict mode, ruff's bandit
   rules and CodeQL ran as on every change.
4. **Release check.** The 0.3.0 files on PyPI were compared with a rebuild of the tag:
   the wheel is identical bit for bit once `SOURCE_DATE_EPOCH` is set to the time the
   release workflow checked out the code; the sdist has the same files with the same
   content, but its archive differs (see SR-3).

## What holds

Each of these was checked in the code, not only in the tests:

- **Write gate.** Write tools carry the `write` tag; `app._WriteGate` hides them from
  both the list and the lookup of a call while `AVENIR_MCP_WRITE` is not `1`, so a
  hidden tool cannot be called by name.
- **Confirmation codes.** A code is `secrets.token_urlsafe(8)` (64 random bits), bound
  to a SHA-256 fingerprint of the plan id and the exact change, valid ten minutes, and
  removed on its first use, even when that use fails, so a code cannot be probed. With
  `AVENIR_MCP_REQUIRE_ELICITATION=1` no code is issued or accepted.
- **Untrusted text.** Payee names and memos pass through `text.untrusted` before they
  reach an answer or a confirmation question: one line, no control, format or
  direction characters, at most 80 characters.
- **Token.** Read into a `SecretStr`; sent only in the `Authorization` header of
  requests to `AVENIR_MCP_YNAB_URL`, which must be `https://` except to this machine;
  httpx does not follow redirects, so the token cannot be sent on elsewhere; every
  path segment is checked against `[A-Za-z0-9][A-Za-z0-9_-]*` before a request is
  built, so an id cannot add, climb or query a path.
- **HTTP transport.** `127.0.0.1` by default; FastMCP's host and origin guard in
  strict mode refuses a `Host` that does not name this machine (421) and a foreign
  `Origin` (403); the bearer token is compared in constant time; writes over HTTP
  refuse to start without a token.
- **Update check.** One GET to `https://pypi.org/pypi/avenir-mcp/json`, no redirects,
  a 1.5-second timeout per step, at most once a day, off with
  `AVENIR_MCP_NO_UPDATE_CHECK=1`, `DO_NOT_TRACK=1` or in CI. Only a version made of
  digits and dots, and higher than the running one, reaches the agent.
- **Journal.** Created with mode `0600` and opened in append mode; a line holds ids,
  and for budget changes the amounts assigned, never a payee, memo or transaction
  amount; lines are read as JSON into strict models, and a damaged line is named.
- **Dependencies.** Locked with hashes; the direct dependency `fastmcp` is pinned
  exactly in the package's metadata, the others to a major version.
- **CI and release.** Every action is pinned by commit; every workflow starts with
  `permissions: {}`; checkouts do not keep credentials; no workflow runs on
  `pull_request_target` or `workflow_run`; PyPI uploads use Trusted Publishing from the
  `pypi` environment, whose deployments the maintainer approves, with PEP 740
  attestations.

## Findings

Severity is rated for avenir-mcp's intended use: one person, on their own machine.

| Id | Severity | Finding | Status |
|---|---|---|---|
| SR-1 | Low | HTTP transport without a token serves the read tools to any local program or user | Fixed after 0.3.0, in the next release |
| SR-2 | Low | Names in a confirmation question are not reduced to one line | Fixed after 0.3.0, in the next release |
| SR-3 | Low | The release build runs tools that are not pinned to a version | Fixed: the build is reproducible and verified in CI (next release) |
| SR-4 | Low | File permission checks apply on Linux and macOS only | Fixed in the documentation |
| SR-5 | Info | An answer to a 2026-07-28 elicitation is not single-use | Open |
| SR-6 | Info | Confirmation codes are shared by every session of a server | Accepted |
| SR-7 | Info | The question of `create_transactions` shows neither memos nor full payees | Open |

### SR-1. HTTP transport without a token (Low)

`AVENIR_MCP_HTTP_TOKEN` is optional in read-only mode. Without it, any program running
on the machine, under any account, can connect to `127.0.0.1:8103` and call the read
tools: balances, transactions, payees. The host and origin guard stops web pages, not
local programs. Other users of the machine are a threat the assurance case names for
the token file and the journal, but not for this port. The HTTP transport is not the
default, and `SECURITY.md` says the token is what makes every request authenticate.

Recommendation: require the token whenever the HTTP transport is used, or at least log
a warning at start-up when it runs without one.

Status: fixed after 0.3.0, in the next release. Every request over HTTP now needs a
token, read-only or not. When `AVENIR_MCP_HTTP_TOKEN` is unset, the server makes a random
one at start-up and prints it once on stderr. A read-only HTTP setup without the variable
has to send that token, or set the variable, after upgrading. Tokens are not checked for
a minimum length.

### SR-2. Names in a confirmation question (Low)

Payees and memos are reduced to one line before they reach a question; other text is
not. The names of categories, groups and accounts come from YNAB as they are, and the
name an agent passes to `create_category` or `update_category` is inserted as given. A
line break in such a name adds a line of the author's choosing to the question the
user reads before saying yes. The change itself is still the one shown and fingerprinted,
and a category is renamed back in one call, so the effect is limited to a misleading
question.

Recommendation: pass every name through `text.untrusted` when building a question,
and refuse control characters in a category name before sending it to YNAB.

Status: fixed after 0.3.0, in the next release. Every confirmation question and preview
shows the names of accounts, categories and groups, and memos, through `text.untrusted`,
and a category name the agent gives with a line break, control or format character is
refused. Each write tool has a test with a name written to forge a line.

### SR-3. Release build tools not pinned (Low)

The `build` job of the `publish` workflow produces the files uploaded to PyPI. It
installs the latest uv (through `setup-uv`), the build backend `setuptools>=77`, and
`twine` with `uv run --with twine`, each resolved when the job runs. A malicious
release of any of them would run in that job and could change the files before they
are uploaded; the attestation would still name this repository's workflow, since it
proves where a file was built, not with what. The 0.3.0 sdist cannot be rebuilt bit for
bit either: setuptools writes the build machine's dates and user into the archive.

Recommendation: pin the build backend and the tools of the build job to exact
versions, make the sdist reproducible, and have the workflow build twice and compare
before uploading, so that anyone can rebuild a release and compare it with PyPI's
files.

Status: fixed for the next release. The build backend is pinned, the wheel and the sdist
are reproducible bit for bit, CI builds twice and compares them on every change, and the
`publish` workflow uploads only when two builds of the tagged commit agree. `SECURITY.md`
says how to rebuild a release and compare it with PyPI's files. uv and twine still come
in their latest versions; a tampered tool would now give files that differ from an
independent rebuild.

### SR-4. File permission checks on Windows (Low)

On Linux and macOS, a `YNAB_API_KEY_FILE` that other users can read is refused, and the
journal is created with mode `0600`. On Windows neither applies: the token file is
accepted whatever its permissions, and the mode has no effect, so the journal is
protected only by the permissions of the folder it is in (by default the user's
profile). `SECURITY.md` stated both protections without that limit.

Status: `SECURITY.md` now says the checks apply on Linux and macOS. The code is
unchanged.

### SR-5. Elicitation answers on protocol 2026-07-28 (Info)

On a 2026-07-28 connection, the client sends the user's answer back with the request
state the server gave it, which is the fingerprint of the preview. The fingerprint
binds the answer to the exact change, but nothing marks it used: a client that sent
the same accepted answer twice would apply the change twice, such as creating the
same transactions again. The MCP client is trusted to relay the user's answers, so
this needs a faulty client rather than a misled agent.

Recommendation: add a random, single-use value to the request state, as the codes
have.

### SR-6. Codes shared across sessions (Info)

Confirmation codes are kept per server process, not per MCP session: over HTTP, a code
issued to one connected client could be spent by another. A server serves one person
(see [Intended use](SECURITY.md#intended-use)) and a code confirms only the exact change
it was issued for, so this changes nothing in intended use. Accepted.

### SR-7. What the question of `create_transactions` shows (Info)

The question lists each new transaction's date, payee, amount and category. The payee
is cut at 80 characters and the memo is not shown, while YNAB receives the full payee
(up to 200 characters) and the memo (up to 500). The code and the fingerprint bind the
full text, so what is created is what was previewed, but the user does not see all of
it before agreeing.

Recommendation: show each memo, cut, in the question.

## Residual risk

Beyond the open findings above, the risks the assurance case already accepts remain:

- A client without elicitation leaves the confirmation code to the agent, and a misled
  model can use it; `AVENIR_MCP_REQUIRE_ELICITATION=1` with a client that supports
  elicitation removes this.
- `approve_transactions` and `import_transactions` act without a preview.
- The YNAB token cannot be narrowed to read-only access, and is readable by any program
  running as the user, through the environment or the token file.
- Over HTTP, traffic on `127.0.0.1` is not encrypted.
- The package's metadata pins `fastmcp` exactly but lets `httpx`, `pydantic`, `mcp` and
  `starlette` move within a major version, so a user's installation may run versions
  newer than those locked and audited here.
- The review was done by the project's author: an independent review would find what
  the author does not see.
