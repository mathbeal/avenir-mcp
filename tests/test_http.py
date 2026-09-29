"""The HTTP transport: only this machine's pages and clients holding the token get in."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from avenir_mcp import http_auth, server

_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    },
}
_TOKEN = "correct-horse-battery-staple"
_GOOD = {"Authorization": f"Bearer {_TOKEN}"}


def _post(headers: dict[str, str], token: str | None = _TOKEN) -> int:
    """POST an initialize request to the app main() would serve; return the status."""
    app = server.mcp.http_app(**server.http_options(SecretStr(token) if token else None))

    async def run() -> int:
        async with app.lifespan(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://127.0.0.1:8103"
            ) as http:
                response = await http.post(
                    "/mcp",
                    json=_INIT,
                    headers={
                        "Accept": "application/json, text/event-stream",
                        **headers,
                    },
                )
                return response.status_code

    return asyncio.run(run())


def test_a_client_with_the_token_gets_in() -> None:
    """Positive control: the right host, no foreign origin, the token."""
    assert _post(_GOOD) == 200


def test_a_foreign_host_is_refused() -> None:
    """DNS rebinding: a web page whose name now points at 127.0.0.1 is refused."""
    assert _post({**_GOOD, "Host": "evil.example:8103"}) == 421


def test_a_foreign_web_page_is_refused() -> None:
    """A page from another site, running in your browser, is refused."""
    assert _post({**_GOOD, "Origin": "https://evil.example"}) == 403


@pytest.mark.parametrize(
    "headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": _TOKEN}]
)
def test_without_the_token_nothing_is_served(headers: dict[str, str]) -> None:
    """No token, a wrong one, or one without its scheme: 401."""
    assert _post(headers) == 401


def test_without_a_token_configured_host_and_origin_are_still_checked() -> None:
    """Read-only over HTTP without a token still refuses other sites."""
    assert _post({}, token=None) == 200
    assert _post({"Origin": "https://evil.example"}, token=None) == 403


def test_writes_over_http_need_a_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """With writes on and no token, the server refuses to start, saying why."""
    monkeypatch.setenv("AVENIR_MCP_TRANSPORT", "http")
    monkeypatch.setenv("AVENIR_MCP_WRITE", "1")
    monkeypatch.delenv("AVENIR_MCP_HTTP_TOKEN", raising=False)
    with (
        patch.object(server.mcp, "run") as run,
        pytest.raises(SystemExit, match="AVENIR_MCP_HTTP_TOKEN"),
    ):
        server.main([])
    run.assert_not_called()


def test_main_serves_http_with_the_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() passes host and origin checks, and the token, to the HTTP server."""
    monkeypatch.setenv("AVENIR_MCP_TRANSPORT", "http")
    monkeypatch.setenv("AVENIR_MCP_WRITE", "1")
    monkeypatch.setenv("AVENIR_MCP_HTTP_TOKEN", _TOKEN)
    with patch.object(server.mcp, "run") as run:
        server.main([])
    kwargs = run.call_args.kwargs
    assert kwargs["host_origin_protection"] is True
    assert [m.cls for m in kwargs["middleware"]] == [http_auth.BearerToken]


def test_messages_other_than_requests_pass_through() -> None:
    """Server start and stop (lifespan) are not requests: the token is not asked for."""
    seen: list[str] = []

    async def inner(scope: dict[str, object], _receive: object, _send: object) -> None:
        seen.append(str(scope["type"]))

    guard = http_auth.BearerToken(inner, SecretStr(_TOKEN))  # type: ignore[arg-type]
    asyncio.run(guard({"type": "lifespan"}, None, None))  # type: ignore[arg-type]
    assert seen == ["lifespan"]


@pytest.mark.ynab_terms
def test_the_token_never_shows_when_printed_or_logged(monkeypatch: pytest.MonkeyPatch) -> None:
    """What main() hands to FastMCP, and the guard itself, print a mask, not the token."""
    monkeypatch.setenv("AVENIR_MCP_TRANSPORT", "http")
    monkeypatch.setenv("AVENIR_MCP_HTTP_TOKEN", _TOKEN)
    with patch.object(server.mcp, "run") as run:
        server.main([])
    options = run.call_args.kwargs
    guard_options = options["middleware"][0].kwargs
    for shown in (repr(options), str(options), repr(guard_options)):
        assert _TOKEN not in shown
