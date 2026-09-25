# Security

## Scope

Avenir holds a YNAB personal access token. That token gives **full read and write
access to every budget of the account**. YNAB offers no read-only scope for personal
tokens. Treat the token like a bank password.

What the server does:

- by default it is **read-only**: tools that change the budget are registered only
  with `AVENIR_MCP_WRITE=1`

- it calls `api.ynab.com` over HTTPS, and nothing else
- it reads the token from the environment and never writes it anywhere
- `apply_categories`, `reconcile_account`, `set_category_budget`, `update_category`
  and `undo_operation` change nothing until the user confirms the
  previewed changes. A confirmation code is single-use, expires after 10 minutes and
  only confirms the exact changes it was issued for
- they record applied operations in a local journal (`AVENIR_MCP_JOURNAL`) holding
  identifiers only, readable by its owner only
- its older write tools (`approve_transactions`, `create_category`,
  `create_transactions`) change your budget **immediately**.
  Keep your MCP client's per-call confirmation on for them.

## Untrusted text and prompt injection

Payee names and memos come from banks, merchants and anyone who can send you
money. A memo can contain text written to manipulate an agent. The server returns
such text as data. Do not give an agent that reads your transactions tools that
can send data elsewhere without reviewing each call.

## Transport

The default transport is stdio: no network port is opened. With
`AVENIR_MCP_TRANSPORT=http`, the server listens on `AVENIR_MCP_HOST`, `127.0.0.1` by default. **Do not bind it to
`0.0.0.0`** or expose it through a container port on all interfaces: anyone who can
reach it can act on your budget. HTTP mode has no authentication and no `Origin`
validation yet (see the roadmap).

## Reporting a vulnerability

Open a [security advisory](https://github.com/mathbeal/avenir-mcp/security/advisories/new).
Please do not open a public issue for a vulnerability.

Expect a first answer within a week.

## Supported versions

The latest release only.
