# Troubleshooting

??? question "My client does not show Avenir's tools"
    - Check the server is connected: `claude mcp list`, or your client's MCP panel.
    - Run `uvx avenir-mcp` in a terminal: it should wait silently for a client. An
      error there is the one your client hides.
    - Restart the client after editing its configuration.

??? question "The tools that change my budget are missing"
    Avenir is read-only unless `AVENIR_MCP_WRITE=1` is in its environment.

??? question "`YNAB 401`"
    The token is wrong or revoked. Create a new one in YNAB's Developer Settings.

??? question "`YNAB 429`"
    YNAB allows 200 requests per hour per token. Wait a few minutes; Avenir's delta
    sync keeps later calls cheap.

??? question "The agent keeps saying `confirmation_required`"
    Your client cannot show a confirmation box, so Avenir returned a preview and a
    code. Tell the agent you agree: it calls the tool again with the code. A code
    lasts 10 minutes and works once.

??? question "`ModuleNotFoundError: avenir_mcp` from a project folder synced by iCloud Drive"
    iCloud can mark files as hidden, and recent Python versions skip hidden `.pth`
    files, which breaks editable installs. Keep the virtual environment outside the
    synced folder: `UV_PROJECT_ENVIRONMENT=~/.local/share/avenir-mcp/venv uv sync`.

??? question "Where do I see what the server does?"
    Set `AVENIR_MCP_LOG_LEVEL=DEBUG`. Diagnostics go to stderr, which your client
    usually keeps in its MCP logs; stdout belongs to the protocol.
