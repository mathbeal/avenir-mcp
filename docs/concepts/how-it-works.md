# How it works

## Amounts

YNAB stores amounts in *milliunits* (1.00 = 1000). Avenir converts at the edge:
every tool takes and returns **currency units**, spending negative. Sums are made in
milliunits inside the server, so rounding never invents a cent.

## Requests and YNAB's rate limit

YNAB allows **200 requests per hour** per token. Avenir keeps a local copy of your
transactions and asks YNAB only for what changed since the last call (*delta sync*).
Most tools cost one or two requests; `suggest_categories` costs two for a whole
page, whatever the number of transactions.

## Errors say what to fix

A malformed argument is refused before YNAB is called, with a message the agent can
act on rather than a bare HTTP error:

```text
--8<-- "snippets/bad_month.json"
```

## Suggestions

A category is suggested when a payee was classified the same way often enough —
90 % of the time by default (`AVENIR_MCP_CONFIDENCE_THRESHOLD`):

- bank labels are **normalised** — card prefixes, invoice dates, masked card numbers,
  references and bank account numbers are removed — so a merchant is recognised
  across its labels;
- money **in** and money **out** are learnt separately;
- only categories you can still use are suggested.

A merchant never classified before gets no suggestion: the agent proposes one and
asks you.

## Forecast

`forecast_balance` separates what recurs from what varies. See
[Plan ahead](../use-cases/plan-ahead.md) for the assumptions it makes and returns.

## Protocol versions

Avenir speaks the current MCP protocol (2026-07-28), where a server asks for
confirmation by returning an *input request* that the client answers on a second
call, and older versions, where it asks during the call. Clients need nothing
special.
