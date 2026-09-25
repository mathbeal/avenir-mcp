# Configuration

Avenir is configured with environment variables, set in your MCP client's `env`
block.

| Variable | Default | Meaning |
|---|---|---|
| `YNAB_API_KEY` | — (**required**) | Your YNAB personal access token. Full read and write access to your budgets. |
| `AVENIR_MCP_WRITE` | unset: read-only | `1` registers the tools that change your budget. |
| `AVENIR_MCP_TRANSPORT` | `stdio` | `stdio` for a client that starts the server; `http` for streamable HTTP. |
| `AVENIR_MCP_HOST` | `127.0.0.1` | HTTP address. Keep it on localhost: the HTTP transport has no authentication. |
| `AVENIR_MCP_PORT` | `8103` | HTTP port. |
| `AVENIR_MCP_JOURNAL` | `$XDG_STATE_HOME/avenir-mcp/journal.jsonl`, else `~/.local/state/avenir-mcp/journal.jsonl` | Journal of applied operations, used by undo. Identifiers only, owner-only permissions. |
| `XDG_STATE_HOME` | `~/.local/state` | Standard location of per-user state; the journal lives under it unless `AVENIR_MCP_JOURNAL` is set. |
| `AVENIR_MCP_CONFIDENCE_THRESHOLD` | `0.90` | Share of a payee's history that must agree before a category is suggested. |
| `AVENIR_MCP_LOG_LEVEL` | `WARNING` | Diagnostics level on stderr (`DEBUG`, `INFO`, …). |
| `AVENIR_MCP_YNAB_URL` | `https://api.ynab.com/v1` | API address; the evaluation points it at a demo budget server. |

## Budget ids

Every tool takes a `budget_id`: an id from `list_budgets`, or `last-used`.

## Running over HTTP

```bash
AVENIR_MCP_TRANSPORT=http YNAB_API_KEY=your-token uvx avenir-mcp
# listening on http://127.0.0.1:8103/mcp
```

Never bind it to `0.0.0.0` or publish the port on all interfaces: anyone who reaches
it acts on your budget.
