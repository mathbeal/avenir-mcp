# Install

## What you need

- **[uv](https://docs.astral.sh/uv/getting-started/installation/)**, which runs Avenir
  without installing anything globally.
- **A YNAB personal access token**:

    1. Open YNAB on the web, then **Account Settings → Developer Settings**.
    2. Under *Personal Access Tokens*, choose **New Token**, confirm with your password.
    3. Copy the token: YNAB shows it only once.

!!! danger "Treat the token like a password"
    A personal access token can **read and change every budget** of your account;
    YNAB offers no read-only token. Keep it out of files you share or commit.

## Add Avenir to your MCP client

The examples below enable the tools that change your budget
(`AVENIR_MCP_WRITE=1`). Leave that line out to keep Avenir strictly read-only.

=== "Claude Code"

    ```bash
    claude mcp add avenir \
      --env YNAB_API_KEY=your-token \
      --env AVENIR_MCP_WRITE=1 \
      -- uvx avenir-mcp
    ```

    Check it is connected with `claude mcp list`, or `/mcp` inside a session.

=== "Claude Desktop"

    Open **Settings → Developer → Edit Config** and add:

    ```json
    {
      "mcpServers": {
        "avenir": {
          "command": "uvx",
          "args": ["avenir-mcp"],
          "env": {
            "YNAB_API_KEY": "your-token",
            "AVENIR_MCP_WRITE": "1"
          }
        }
      }
    }
    ```

    Restart Claude Desktop.

=== "Cursor"

    In `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (one project):

    ```json
    {
      "mcpServers": {
        "avenir": {
          "command": "uvx",
          "args": ["avenir-mcp"],
          "env": { "YNAB_API_KEY": "your-token", "AVENIR_MCP_WRITE": "1" }
        }
      }
    }
    ```

=== "VS Code"

    In `.vscode/mcp.json`:

    ```json
    {
      "servers": {
        "avenir": {
          "type": "stdio",
          "command": "uvx",
          "args": ["avenir-mcp"],
          "env": { "YNAB_API_KEY": "your-token", "AVENIR_MCP_WRITE": "1" }
        }
      }
    }
    ```

!!! tip "Before the first PyPI release"
    Replace `uvx avenir-mcp` with
    `uvx --from git+https://github.com/mathbeal/avenir-mcp avenir-mcp`.

## Check it works

Ask your client:

> List my YNAB budgets.

It should call `list_budgets` and answer with your budgets' names:

```json
--8<-- "snippets/list_budgets.json"
```

(That is the demo budget used throughout this documentation.)

If nothing happens, see [Troubleshooting](../troubleshooting.md).
