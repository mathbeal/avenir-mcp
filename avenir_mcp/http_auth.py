"""A bearer token for the HTTP transport, so only clients you configured get in."""

from __future__ import annotations

import secrets

from starlette.datastructures import Headers  # pylint: disable=import-error
from starlette.middleware import Middleware  # pylint: disable=import-error
from starlette.responses import PlainTextResponse  # pylint: disable=import-error
from starlette.types import ASGIApp, Receive, Scope, Send  # pylint: disable=import-error


class BearerToken:  # pylint: disable=too-few-public-methods
    """Refuse every HTTP request whose Authorization header is not `Bearer <token>`."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        """Wrap an ASGI application.

        Args:
            app: The application to protect.
            token: The token every request must carry.
        """
        self.app = app
        self.expected = f"Bearer {token}".encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass an HTTP request on only if it carries the token; answer 401 otherwise.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive channel.
            send: The ASGI send channel.
        """
        if scope["type"] == "http":
            given = Headers(scope=scope).get("authorization", "").encode()
            if not secrets.compare_digest(given, self.expected):
                refusal = PlainTextResponse(
                    "Unauthorized: send the header Authorization: Bearer <AVENIR_MCP_HTTP_TOKEN>.",
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await refusal(scope, receive, send)
                return
        await self.app(scope, receive, send)


def middleware(token: str | None) -> list[Middleware]:
    """Build the token check for the HTTP transport.

    Args:
        token: AVENIR_MCP_HTTP_TOKEN, or None.

    Returns:
        The check when a token is configured, nothing otherwise.
    """
    return [Middleware(BearerToken, token=token)] if token else []
