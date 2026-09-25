# Agent contract

This file tells an automated agent how to work in this repository. It is the
contract; `CLAUDE.md` points here. The rules apply to humans as well.

## What the code is

An MCP server between an agent and the YNAB API. Four modules:

- `client.py` talks HTTP to YNAB and is the only place that knows about milliunits
  on the way in
- `analytics.py` and `classifier.py` compute; they never call the network
  themselves
- `server.py` declares the MCP tools and nothing else

## Rules that hold everywhere

**No secret, ever.** The YNAB token grants full write access to a person's
budgets. It is never logged, printed, returned in a tool result or committed.
`tests/test_hygiene.py` fails on an IBAN, a token or a bank statement in the tree.

**No real financial data.** Fixtures use invented accounts, payees and amounts.
A test that needs realistic data gets invented realistic data. Documentation
examples come only from `python -m docsgen`, which runs Avenir on the invented demo
budget in `evals/`: never paste an answer from a real budget.

**Tool output is for an agent.** Keep it short, name things plainly, and say in the
docstring when to use the tool and what unit its amounts are in. A tool description
is part of the interface: change it with the same care as a signature.

**Writes are consequential.** A tool that modifies a budget says so in its
docstring. The roadmap makes every write previewable and undoable; do not add a
write path that would be hard to fit into that.

**Transaction text is untrusted.** Memos and payee names come from banks and
strangers. Return them as data; never splice them into instructions.

**stdout belongs to the protocol.** In stdio mode, anything else written to stdout
corrupts the session. Diagnostics go through `logging`, on stderr.

**Few dependencies.** `fastmcp` and `httpx`, pinned. Adding one needs a reason
written in the pull request.

**Tests come first.** Write the failing test, watch it fail, then write the code.
Coverage is enforced at 100 %, branches included.

## Before opening a pull request

```bash
uv sync
just check              # lint, types, tests at 100 %, vocabulary, lockfile
uv run python -m docsgen  # when a tool, resource, prompt or answer changed
just docs               # the site builds in EN, FR and ES, every link valid
```

A test fails when the generated tool reference or an example no longer matches the
code, and when a hand-written page is missing in French or Spanish. When a change affects how an agent uses the tools, run
`just evaluate` (a real agent on the demo budget) and commit its report.
