# Avenir — an MCP server for YNAB

[![quality](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml/badge.svg)](https://github.com/mathbeal/avenir-mcp/actions/workflows/quality.yml)
[![python](https://img.shields.io/badge/python-3.14-blue)](https://github.com/mathbeal/avenir-mcp)
[![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/mathbeal/avenir-mcp)
[![licence](https://img.shields.io/badge/licence-MIT-blue)](https://github.com/mathbeal/avenir-mcp/blob/main/LICENSE)

> 🇬🇧 **Avenir** (French for *the future*) lets an AI agent read your YNAB budget
> and help you plan what comes next.
>
> 🇫🇷 **Avenir** permet à un agent IA de lire votre budget YNAB et de vous aider
> à préparer la suite.

Give an AI agent your budget — the balances, the trends, the transactions waiting
to be classified — and let it help you plan what comes next.

Avenir is a [Model Context Protocol](https://modelcontextprotocol.io) server for
[YNAB](https://www.ynab.com). It works with Claude Desktop, Claude Code, Cursor and
any MCP client.

> **Not affiliated with or endorsed by YNAB.** YNAB and You Need A Budget are
> registered trademarks of YNAB.

**Status: alpha (0.1).** The tools work and are tested, but they are still close to
the YNAB API. The [roadmap](ROADMAP.md) turns them into task-level tools that are
read-only by default, previewable and undoable.

## What it does

| Tool | Kind | What for |
|---|---|---|
| `list_budgets` | read | the budgets your token can see |
| `list_accounts` | read | accounts and balances |
| `list_category_groups` | read | where a new category can go |
| `get_monthly_summary` | read | the month at a glance: income, budgeted, spent, Ready to Assign, overspent categories |
| `get_category_balances` | read | budgeted, spent and available per category, empty ones left out unless asked |
| `get_budget_vs_actual` | read | how much of each category's budget is spent |
| `get_spending_trends` | read | spending per category over the last N months |
| `suggest_categories` | read | **start here to classify**: pending transactions, newest first, paginated, with a suggestion when the payee's history allows, and the category list, in two YNAB requests |
| `forecast_balance` | read | project the balance month by month up to 24 months ahead and name the first month it goes below zero; every assumption (recurring charges found in your history, average spending and income, your one-off amounts) is returned so you can correct it |
| `apply_categories` | **write, confirmed, undoable** | assign categories to many transactions: previewed, confirmed by the user, then journaled |
| `undo_operation` | **write, confirmed** | revert the latest operation (or a named one); never overwrites a later change |
| `reconcile_account` | **write, confirmed, undoable** | compare an account with the balance your bank shows; explain a gap (pending transactions, the one matching the difference, likely duplicates) without writing; once it matches, mark cleared transactions reconciled; an adjustment only on explicit request |
| `update_category` | **write, confirmed** | rename a category or move it to another group; the result gives the previous name and group to revert |
| `approve_transactions` | **write** | mark transactions as reviewed |
| `create_category` | **write** | add a category |
| `set_category_budget` | **write, confirmed, undoable** | set the amount budgeted in a category for a month; previewed as before → after |
| `create_transactions` | **write** | add transactions, e.g. to fill an import gap |

## Install

The examples enable write tools (`AVENIR_MCP_WRITE=1`); drop it to keep the server
read-only.

You need [uv](https://docs.astral.sh/uv/) and a YNAB personal access token
(YNAB → Account Settings → Developer Settings).

Until the first PyPI release, install from GitHub:

```json
{
  "mcpServers": {
    "avenir": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mathbeal/avenir-mcp", "avenir-mcp"],
      "env": { "YNAB_API_KEY": "your-token", "AVENIR_MCP_WRITE": "1" }
    }
  }
}
```

With Claude Code:

```bash
claude mcp add avenir --env YNAB_API_KEY=your-token --env AVENIR_MCP_WRITE=1 -- uvx --from git+https://github.com/mathbeal/avenir-mcp avenir-mcp
```

## Environment variables

| Variable | Required | Default | Used by | Meaning |
|---|---|---|---|---|
| `YNAB_API_KEY` | **yes** | — | every tool | YNAB personal access token. It grants full read and write access to your budgets: keep it in your MCP client's `env` block or in a `.env` file, never in the repository. |
| `AVENIR_MCP_WRITE` | no | unset (read-only) | write tools | `1` registers the tools that change your budget. Without it the server is read-only: write tools are neither listed nor callable. |
| `AVENIR_MCP_TRANSPORT` | no | `stdio` | `avenir-mcp` command | `stdio` for a client that launches the server itself (Claude Desktop, Claude Code, Cursor); `http` to serve streamable HTTP. |
| `AVENIR_MCP_HOST` | no | `127.0.0.1` | HTTP transport | Address to listen on. Keep it on localhost: the HTTP transport has no authentication yet. |
| `AVENIR_MCP_PORT` | no | `8103` | HTTP transport | Port to listen on. |
| `AVENIR_MCP_JOURNAL` | no | `$XDG_STATE_HOME/avenir-mcp/journal.jsonl`, else `~/.local/state/avenir-mcp/journal.jsonl` | `apply_categories`, `reconcile_account`, `undo_operation` | File recording applied operations so they can be undone. Holds identifiers only (transaction and category ids), no amounts or payees; created with owner-only permissions. |
| `AVENIR_MCP_CONFIDENCE_THRESHOLD` | no | `0.90` | `suggest_categories` | Share of a payee's past transactions that must fall in one category (0 to 1) before a single category is proposed with `auto_classify: true`. Below it, the top three candidates are returned for review. |

Every tool takes a `budget_id`: a budget UUID from `list_budgets`, or `last-used`.

## Limits

Written down so that nobody discovers them the hard way:

- **Confirmed writes.** `apply_categories` and `undo_operation` show what will change
  and wait for the user: through the client's confirmation dialog (MCP elicitation)
  when it has one, otherwise through a single-use code valid 10 minutes for exactly the
  previewed changes.
- **Read-only by default.** Write tools exist only with `AVENIR_MCP_WRITE=1`.
- **Older write tools still act immediately** once writes are enabled:
  `approve_transactions`, `create_category`, `create_transactions`.
- Undo covers operations made with `apply_categories`, `reconcile_account` and
  `set_category_budget`, and only on the machine whose
  journal recorded them. An undo cannot itself be undone.
- `create_transactions` creates transactions that are already approved and cleared.
- Amounts are in currency units everywhere (YNAB's milliunits stay inside the server).
- Suggestions come from your own history, learnt separately for money in and money
  out, and only point to categories you can still assign. A merchant never classified
  before gets no suggestion, and the agent chooses from the category list. YNAB allows 200 requests
  per hour; `suggest_categories` uses two per page.
- `forecast_balance` extrapolates your last months: recurring charges must appear in
  3 of the last 4 months at a stable amount, and averages include one-off money
  (a capital injection, a yearly tax). Read its assumptions before its conclusion.
- Transaction memos and payee names come from your bank and are untrusted text. See
  [SECURITY.md](SECURITY.md).

## Tests and coverage

| Measure | Value |
|---|---|
| Tests | 220, none of which calls the YNAB API; some go through the MCP protocol itself |
| Line coverage | 100 % (1080 statements) |
| Branch coverage | 100 % (234 branches) |
| Type checking | mypy `strict` |
| Lint | pylint 10.00/10, black, isort |
| Vocabulary | lexdrift, against the accepted baseline `lexdrift.lock` |
| Supply chain | pip-audit on the locked dependencies, zizmor on the workflows |

Coverage below 100 % fails the test run (`--cov-fail-under=100`, branches included).
`tests/test_hygiene.py` also fails if an IBAN, a YNAB token or a bank statement ever
lands in the repository.

## Development

```bash
git clone https://github.com/mathbeal/avenir-mcp
cd avenir-mcp
uv sync
uv run pytest            # fails under 100 % line and branch coverage
uv run mypy
uv run black --check avenir_mcp tests && uv run isort --check avenir_mcp tests
uv run pylint avenir_mcp tests
uvx lexdrift check avenir_mcp --baseline lexdrift.lock
```

CI (`.github/workflows/quality.yml`) runs the same, plus the lockfile check, typos,
zizmor and pip-audit.

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before opening a
pull request.

## Licence

MIT.
