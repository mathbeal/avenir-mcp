# Security

## Scope

avenir-mcp holds a YNAB personal access token. That token gives **full read and write
access to every budget of the account**. YNAB offers no read-only scope for personal
tokens. Treat the token like a bank password.

What the server does:

- by default it is **read-only**: tools that change the budget are registered only
  with `AVENIR_MCP_WRITE=1`

- it calls `api.ynab.com` over HTTPS, and nothing else
- it reads the token from the environment, or from `YNAB_API_KEY_FILE` (a file readable
  by its owner only, else refused), and never writes it anywhere
- `apply_categories`, `reconcile_account`, `set_category_budget`, `update_category`,
  `create_transactions`, `create_category`, `split_transaction` and `undo_operation` change nothing until the user confirms the
  previewed changes. A confirmation code is single-use, expires after 10 minutes and
  only confirms the exact changes it was issued for
- with `AVENIR_MCP_REQUIRE_ELICITATION=1`, only the user's yes given in the client
  confirms a write: codes, which an agent could relay alone, are disabled
- a client that cannot ask the user (no MCP elicitation) leaves the code to the agent.
  Every code comes with the instruction that only the user can agree, never a payee or
  a memo, but a model can still be misled: in the evaluation, one model out of eight
  used a code on its own after reading a planted memo, then undid the change. Use a
  client that supports elicitation, with `AVENIR_MCP_REQUIRE_ELICITATION=1`
- they record applied operations in a local journal (`AVENIR_MCP_JOURNAL`) holding
  identifiers, and the amounts a budget change assigned before and after, readable by
  its owner only
- `approve_transactions` acts immediately: it only marks transactions as reviewed.
  Keep your MCP client's per-call confirmation on for it.
- `import_transactions` acts immediately too: it asks YNAB to import what the linked
  banks already have, as the app's Import does, and deletes or changes nothing.

## Untrusted text and prompt injection

Payee names and memos come from banks, merchants and anyone who can send you
money. A memo can contain text written to manipulate an agent. The server returns
such text as data. Do not give an agent that reads your transactions tools that
can send data elsewhere without reviewing each call.

## Transport

The default transport is stdio: no network port is opened. With
`AVENIR_MCP_TRANSPORT=http`, the server listens on `AVENIR_MCP_HOST`, `127.0.0.1` by default. **Do not bind it to
`0.0.0.0`** or expose it through a container port on all interfaces: the traffic is
plain HTTP. Over HTTP, requests whose `Host` or `Origin` header does not name this
machine are refused (against DNS rebinding), and with `AVENIR_MCP_HTTP_TOKEN` set every
request must carry `Authorization: Bearer <token>`. Writes over HTTP require the token:
without it the server refuses to start.

## Intended use

avenir-mcp runs for one person, on their machine, with their own YNAB token. Running it as
a public or shared server is not supported: it has no user accounts, and YNAB's API terms
require OAuth for an application used by others. Reports about such deployments are
out of scope.

## Untrusted text in answers

Payee names and memos are shown on one line, without control, zero-width or
direction-override characters, and cut at 80 characters: bank text cannot add a forged
line to a confirmation question. Amounts passed by an agent must be finite and within a
billion either way. `AVENIR_MCP_YNAB_URL` must use `https://`, except for `127.0.0.1` and
`localhost`, so the token never travels in clear.

## Reporting a vulnerability

Open a [security advisory](https://github.com/mathbeal/avenir-mcp/security/advisories/new).
Please do not open a public issue for a vulnerability.

Expect a first answer within a week.

## Supported versions

The latest release only.
