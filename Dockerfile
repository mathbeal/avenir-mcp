# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

# avenir-mcp as a container, for a client that starts an MCP server with `docker run -i`
# and for Docker's MCP catalogue, which builds this file itself and lists the tools the
# image answers with.
#
# The image starts with no YNAB_API_KEY, which the client passes in, and read-only:
# AVENIR_MCP_WRITE is left unset, so the container answers questions and changes no plan
# until its operator says otherwise.
#
# Two stages: the first installs exactly the versions uv.lock pins and nothing else, the
# second carries only the environment that came out of it, so neither uv, nor the build
# files, nor a development tool ships. Both images are pinned by digest, as every image
# and action of this repository is; the tag beside each digest says which release it is.

FROM python:3.14-slim@sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8 AS build

# uv, as one binary from its own image: nothing is installed into the Python to get it.
COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /usr/local/bin/uv

# UV_FROZEN: install uv.lock as it is, and fail rather than resolve the dependencies
# again, so the image holds the versions this repository tests.
# UV_PYTHON_DOWNLOADS: the Python of the base image, not one fetched during the build.
# UV_COMPILE_BYTECODE: the .pyc files are written here, once, rather than at each start.
# UV_LINK_MODE: copy, since the cache and the target are not on the same filesystem.
ENV UV_FROZEN=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# What building the wheel reads: the metadata, the lock, the package, and the two files
# pyproject.toml names, its readme and its licence.
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY avenir_mcp ./avenir_mcp

# --no-dev: the test and lint tools stay out of an image that faces a reader's budget.
# --no-editable: the package is copied into the environment, so the sources below /app
# are not needed at run time and the next stage leaves them behind.
RUN uv sync --no-dev --no-editable

FROM python:3.14-slim@sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8

LABEL org.opencontainers.image.title="avenir-mcp" \
      org.opencontainers.image.description="Unofficial MCP server for YNAB: budgets, spending and transaction classification, built for agents." \
      org.opencontainers.image.source="https://github.com/mathbeal/avenir-mcp" \
      org.opencontainers.image.documentation="https://avenir-mcp.pages.dev/avenir-mcp/getting-started/install/" \
      org.opencontainers.image.licenses="MIT"

# A user of its own, with a home: nothing the server does needs root, and the journal of
# an operator who enabled writes is written under that home. It lives as long as the
# container does, so a client that wants to undo an operation after a restart mounts a
# volume on it.
RUN useradd --create-home --uid 10001 avenir

# The environment built above, at the path its scripts were written for, owned by root:
# the account the server runs under cannot change what it runs.
COPY --from=build /app/.venv /app/.venv

# PATH: `avenir-mcp` is the environment's own console script.
# PYTHONDONTWRITEBYTECODE: the bytecode is already in the layer above.
# PYTHONUNBUFFERED: in stdio mode an answer is a line on stdout; none waits in a buffer.
ENV PATH="/app/.venv/bin:$PATH" \
    HOME="/home/avenir" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER avenir
WORKDIR /home/avenir

# stdio, the server's own default: an operator who wants the HTTP transport instead
# passes AVENIR_MCP_TRANSPORT=http, as with any other way of installing avenir-mcp.
ENTRYPOINT ["avenir-mcp"]
