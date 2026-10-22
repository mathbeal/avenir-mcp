# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The one-click install links of the documentation, from one configuration.

Cursor, LM Studio and VS Code each install an MCP server from a link that carries the
server's configuration, so the reader clicks once instead of editing a JSON file. The
three formats come from their publishers' documentation:

- Cursor, "MCP install links": `cursor://anysphere.cursor-deeplink/mcp/install?name=…`
  `&config=…`, the entry as base64 — https://cursor.com/docs/mcp/install-links
- LM Studio, "Add to LM Studio button": `lmstudio://add_mcp?name=…&config=…`, the same
  base64, URL-encoded — https://lmstudio.ai/docs/app/mcp/deeplink
- VS Code, "Create an MCP installation URL": `vscode:mcp/install?…`, the whole payload
  URL-encoded JSON, the server's name and the prompts it asks for inside it —
  https://code.visualstudio.com/api/extension-guides/ai/mcp#create-an-mcp-installation-url

Every link installs avenir-mcp read-only: no `AVENIR_MCP_WRITE`. A link never holds a
real token. Cursor and LM Studio cannot ask for one, so their links carry the same
placeholder the page's manual configuration shows, and the page says where to replace
it; VS Code asks for it in a password box and keeps it in its secret storage.

`python -m docsgen.install` prints every link, and `tests/test_install_links.py` decodes
the ones written in the README and the install pages: a link that drifts from the
configuration below fails the test.
"""

from __future__ import annotations

import base64
import json
from urllib.parse import quote

NAME = "avenir-mcp"
COMMAND = "uvx"

# The token as each language's install page writes it, to replace after the one click.
PLACEHOLDERS = {
    "": "your-token",
    "fr": "votre-jeton",
    "es": "su-token",
    "de": "ihr-token",
    "nl": "uw-token",
}

# VS Code's password box: the identifier the configuration refers to, and its prompt.
# INPUT_ID, not a name with "token" in it: ruff reads such an assignment as a secret.
# German and Dutch keep YNAB's own label, as the pages do.
INPUT_ID = "ynab-token"
PROMPTS = {
    "": "YNAB personal access token",
    "fr": "Jeton d'accès personnel YNAB",
    "es": "Token de acceso personal de YNAB",
    "de": "YNAB Personal Access Token",
    "nl": "Persoonlijk YNAB-toegangstoken",
}


def server(token: str) -> dict[str, object]:
    """avenir-mcp as an MCP client configures it: the entry under its name.

    Args:
        token: What the client passes as YNAB_API_KEY — a placeholder, or a
            reference to a value the client asks for.

    Returns:
        The command, its arguments and its environment, read-only.
    """
    return {"command": COMMAND, "args": [NAME], "env": {"YNAB_API_KEY": token}}


def _base64(configuration: dict[str, object]) -> str:
    """The configuration as JSON, base64, the way both editors' generators encode it.

    Args:
        configuration: The entry to encode.

    Returns:
        Its base64, padding included.
    """
    compact = json.dumps(configuration, separators=(",", ":"), ensure_ascii=False)
    return base64.b64encode(compact.encode("utf-8")).decode("ascii")


def cursor(language: str) -> str:
    """The link that adds avenir-mcp to Cursor.

    Args:
        language: "" for English, or a translation's code.

    Returns:
        The deeplink, the configuration base64 in its `config` parameter.
    """
    config = _base64(server(PLACEHOLDERS[language]))
    return f"cursor://anysphere.cursor-deeplink/mcp/install?name={NAME}&config={config}"


def lm_studio(language: str) -> str:
    """The link that adds avenir-mcp to LM Studio.

    Args:
        language: "" for English, or a translation's code.

    Returns:
        The deeplink, the base64 URL-encoded as LM Studio's generator writes it.
    """
    config = quote(_base64(server(PLACEHOLDERS[language])), safe="")
    return f"lmstudio://add_mcp?name={NAME}&config={config}"


def vs_code(language: str) -> str:
    """The link that adds avenir-mcp to VS Code, which asks for the token itself.

    Args:
        language: "" for English, or a translation's code.

    Returns:
        The deeplink, its whole payload URL-encoded JSON: the server's name, its
        configuration, and the password box VS Code shows at the first start.
    """
    payload = {
        "name": NAME,
        "type": "stdio",
        **server(f"${{input:{INPUT_ID}}}"),
        "inputs": [
            {
                "type": "promptString",
                "id": INPUT_ID,
                "description": PROMPTS[language],
                "password": True,
            }
        ],
    }
    compact = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return f"vscode:mcp/install?{quote(compact, safe='')}"


def links(language: str) -> dict[str, str]:
    """Every one-click link of one language.

    Args:
        language: "" for English, or a translation's code.

    Returns:
        Each editor and its link.
    """
    return {
        "cursor": cursor(language),
        "lm_studio": lm_studio(language),
        "vs_code": vs_code(language),
    }


def snippet(language: str) -> str:
    """The links of one language, as the install page imports them.

    A page holding a base64 by hand would drift from the configuration at the first
    change; it imports this file instead, which `python -m docsgen` writes.

    Args:
        language: "" for English, or a translation's code.

    Returns:
        The JSON of that language's three links.
    """
    return json.dumps(links(language), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    for code in PLACEHOLDERS:
        print(f"[{code or 'en'}]")
        for editor, link in links(code).items():
            print(f"{editor}: {link}")
