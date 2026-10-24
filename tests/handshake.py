# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Speak MCP over stdio to a server started as a child process, and read its tools.

This is the handshake a client makes: `initialize`, the notification that follows it,
then `tools/list`. The tests that use it start the server the way one way of installing
it does (the Claude Desktop launcher, the container) and check what comes back, so a
packaging that does not run is a failing test rather than a report from a reader.
"""

from __future__ import annotations

import json
import subprocess  # noqa: S404  # nosec B404 - starts avenir-mcp, packaged here
import threading
from typing import IO, TYPE_CHECKING

from avenir_mcp import __version__

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

# A server that never answers must fail the suite rather than hold it: the handshake
# takes under a second once the server is up, and the process is killed well before a
# runner gives up. A container has an image to start, hence the same wide margin.
TIMEOUT = 120.0

# What the two requests of the handshake carry.
PARAMS: dict[str, dict[str, object]] = {
    "initialize": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "avenir-mcp's tests", "version": __version__},
    },
    "tools/list": {},
}


def tools_listed(command: Sequence[str], environment: Mapping[str, str] | None = None) -> list[str]:
    """Start a server with this command, make the handshake, and read back its tools.

    Args:
        command: The command that starts avenir-mcp, as a client would run it.
        environment: The environment to start it with; None to inherit this process's.

    Returns:
        The names of the tools the server lists, in the order it lists them.

    Raises:
        AssertionError: If the server stops before answering, or names itself something
            other than the release this repository is.
    """
    process = subprocess.Popen(  # noqa: S603  # nosec B603 - avenir-mcp, packaged here
        list(command),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        # stdout belongs to the protocol; the banner and the logs go to stderr.
        stderr=subprocess.DEVNULL,
        env=None if environment is None else dict(environment),
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    # The context manager closes the three pipes and waits; the timer makes sure there
    # is something to wait for, whatever the server does.
    with process:
        assert process.stdin and process.stdout
        killer = threading.Timer(TIMEOUT, process.kill)
        killer.start()
        try:
            return _handshake(process.stdin, process.stdout)
        finally:
            killer.cancel()
            process.kill()


def _handshake(to_server: IO[str], from_server: IO[str]) -> list[str]:
    """Initialise the session, then ask for the tools, one JSON object per line.

    Args:
        to_server: The server's standard input.
        from_server: The server's standard output.

    Returns:
        The names of the tools the server lists.

    Raises:
        AssertionError: If the server stops before answering, or names itself something
            other than the release this repository is.
    """

    def ask(identifier: int, method: str) -> Mapping[str, object]:
        request = {"jsonrpc": "2.0", "id": identifier, "method": method, "params": PARAMS[method]}
        to_server.write(f"{json.dumps(request)}\n")
        to_server.flush()
        for line in from_server:
            answer = json.loads(line)
            if answer.get("id") == identifier:
                result = answer["result"]
                assert isinstance(result, dict), answer
                return result
        raise AssertionError(f"the server stopped before answering {method}")

    about = ask(1, "initialize")["serverInfo"]
    assert about == {"name": "avenir-mcp", "version": __version__}, about
    to_server.write(f"{json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'})}\n")
    to_server.flush()
    listed = ask(2, "tools/list")["tools"]
    assert isinstance(listed, list)
    return [tool["name"] for tool in listed]
