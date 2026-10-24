# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""The container starts avenir-mcp without a token, read-only, as a user that is not root.

Docker's MCP catalogue builds the `Dockerfile` of this repository itself and lists the
tools the image answers with. The tests below read the file, and the one that needs an
image built from it runs in CI, where `AVENIR_MCP_DOCKER_IMAGE` names it.
"""

from __future__ import annotations

import asyncio
import os
import re
import tomllib
from pathlib import Path

import pytest
import yaml

from avenir_mcp import server
from tests import handshake

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
DOCKERIGNORE = (ROOT / ".dockerignore").read_text(encoding="utf-8")
WORKFLOW = yaml.safe_load((ROOT / ".github" / "workflows" / "quality.yml").read_text("utf-8"))
# The job that builds the image, and the one check branch protection requires.
JOB = "docker"
AGGREGATE = "passed"
# Set by that job to the tag it built; the live handshake is skipped without it.
IMAGE = os.getenv("AVENIR_MCP_DOCKER_IMAGE")
# What the image must not carry: a token belongs to the client that starts the container,
# and writes are the operator's decision, not the packaging's.
NEVER_IN_THE_IMAGE = ("YNAB_API_KEY", "AVENIR_MCP_WRITE", "AVENIR_MCP_HTTP_TOKEN")
# Directories that would make the build context heavy and the image no more useful.
LEFT_OUT = (".git", ".venv", "benchmarks", "docs", "evals", "mcpb", "plugin", "tests")


def _lines() -> list[str]:
    """Every instruction of the Dockerfile, one per line, continuations joined.

    Returns:
        The instructions, comments and blank lines removed.
    """
    joined = re.sub(r"\\\s*\n\s*", " ", DOCKERFILE)
    kept = [line.strip() for line in joined.splitlines()]
    return [line for line in kept if line and not line.startswith("#")]


def _instruction(name: str) -> list[str]:
    """The arguments of every occurrence of one instruction.

    Args:
        name: The instruction, such as FROM or COPY.

    Returns:
        What follows it, once per occurrence, in the order of the file.
    """
    return [
        line[len(name) :].strip()
        for line in _lines()
        if line.upper().startswith(f"{name.upper()} ")
    ]


def _environment() -> dict[str, str]:
    """Every variable the image sets, whichever ENV instruction sets it.

    Returns:
        The variables, by name.
    """
    pairs = {}
    for arguments in _instruction("ENV"):
        for name, value in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)=("[^"]*"|\S+)', arguments):
            pairs[name] = value.strip('"')
    return pairs


def _copied() -> list[str]:
    """Every path of the repository the Dockerfile copies into the image.

    Returns:
        The sources of each COPY that reads the build context, destinations left out.
    """
    sources = []
    for arguments in _instruction("COPY"):
        parts = [part for part in arguments.split() if not part.startswith("--")]
        if "--from=" not in arguments:
            sources += parts[:-1]
    return sources


def _reincluded() -> list[str]:
    """The entries `.dockerignore` puts back into the context after excluding everything.

    Returns:
        The paths, without their leading `!`.
    """
    return [
        line.strip().removeprefix("!")
        for line in DOCKERIGNORE.splitlines()
        if line.strip().startswith("!")
    ]


def _job() -> dict[str, object]:
    """The workflow job that builds the image.

    Returns:
        Its definition.
    """
    job = WORKFLOW["jobs"][JOB]
    assert isinstance(job, dict)
    return job


def _commands() -> list[str]:
    """Every shell line the building job runs.

    Returns:
        The lines, one per line, whatever step they belong to.
    """
    steps = _job()["steps"]
    assert isinstance(steps, list)
    return [line.strip() for step in steps for line in step.get("run", "").splitlines()]


def test_both_stages_run_a_python_the_package_supports() -> None:
    """A base image older than `requires-python` would build an image that cannot start."""
    package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lowest = package["project"]["requires-python"].removeprefix(">=")
    pythons = [line for line in _instruction("FROM") if line.startswith("python:")]
    assert pythons, _instruction("FROM")
    for image in pythons:
        version = re.match(r"python:(\d+)\.(\d+)-slim@sha256:[0-9a-f]{64}", image)
        assert version, image
        assert tuple(map(int, version.groups())) >= tuple(map(int, lowest.split("."))), image


def test_every_image_the_build_pulls_is_pinned_by_digest() -> None:
    """A tag moves; a digest does not. Docker's catalogue rebuilds this file on its own."""
    pulled = _instruction("FROM") + [
        argument for argument in _instruction("COPY") if "--from=ghcr.io/" in argument
    ]
    for line in pulled:
        reference = line.split(" AS ")[0].split("--from=")[-1].split()[0]
        assert re.search(r"@sha256:[0-9a-f]{64}$", reference), line


def test_the_image_installs_the_versions_the_lock_pins() -> None:
    """`uv sync` with UV_FROZEN fails rather than resolve again: the image is the lock."""
    assert "uv.lock" in _copied()
    assert _environment()["UV_FROZEN"] == "1"
    assert any(line.startswith("uv sync") for line in _instruction("RUN"))


def test_the_build_installs_no_development_tool() -> None:
    """pytest, ruff and mypy have no reason to ship in front of a reader's budget."""
    syncs = [line for line in _instruction("RUN") if line.startswith("uv sync")]
    assert syncs
    for line in syncs:
        assert "--no-dev" in line, line


def test_everything_the_dockerfile_copies_is_in_the_build_context() -> None:
    """A path `.dockerignore` excludes makes the build fail, not the image smaller."""
    for source in _copied():
        assert (ROOT / source).exists(), source
        assert source in _reincluded(), source


def test_the_build_context_holds_nothing_the_image_does_not_install() -> None:
    """Everything is excluded first, so the tests, the docs and the history stay out."""
    rules = [line.strip() for line in DOCKERIGNORE.splitlines() if not line.startswith("#")]
    assert next(rule for rule in rules if rule) == "*"
    for name in LEFT_OUT:
        assert name not in _reincluded(), name


def test_the_container_runs_as_a_user_that_is_not_root() -> None:
    """Nothing the server does needs root; a container that drops it limits a break-in."""
    users = _instruction("USER")
    assert users, "the image would run as root"
    assert users[-1] not in {"root", "0"}


def test_the_container_starts_the_server_over_stdio_and_nothing_else() -> None:
    """A client starts it with `docker run -i`: the entry point is the server itself."""
    assert _instruction("ENTRYPOINT") == ['["avenir-mcp"]']
    assert not _instruction("CMD")
    # The server's own default; an operator asks for HTTP with AVENIR_MCP_TRANSPORT.
    assert "AVENIR_MCP_TRANSPORT" not in _environment()


def test_the_image_carries_neither_a_token_nor_permission_to_change_a_plan() -> None:
    """Read-only until its operator says otherwise, and no secret baked into a layer."""
    for name in NEVER_IN_THE_IMAGE:
        assert name not in _environment(), name
        assert name not in " ".join(_instruction("ARG")), name


def test_a_workflow_builds_the_image_and_asks_it_for_its_tools() -> None:
    """The image is checked where it is built, and the required check waits for it."""
    commands = _commands()
    assert any(line.startswith("docker build ") for line in commands), commands
    assert any("tests/test_docker.py" in line for line in commands), commands
    assert JOB in WORKFLOW["jobs"][AGGREGATE]["needs"]


def test_building_the_image_is_one_just_recipe() -> None:
    """What CI does is what a contributor can run: the same build, the same handshake."""
    recipe = (ROOT / "justfile").read_text(encoding="utf-8")
    assert "\ndocker:\n" in recipe
    gates = re.search(r"^check: (.*)$", recipe, re.MULTILINE)
    assert gates
    # Separate from `just check`, which needs no Docker and no image to build.
    assert "docker" not in gates.group(1).split()


@pytest.mark.skipif(not IMAGE, reason="no image built: AVENIR_MCP_DOCKER_IMAGE is unset")
def test_the_container_starts_without_a_token_and_lists_its_read_only_tools() -> None:
    """Docker lists the tools at build time, with no YNAB account and no token to use."""
    every = asyncio.run(server.mcp.list_tools())
    read_only = sorted(tool.name for tool in every if server.WRITE_TAG not in tool.tags)
    listed = handshake.tools_listed(
        # No --env: the container starts with nothing of this machine's environment.
        ["docker", "run", "--rm", "--interactive", str(IMAGE)]
    )
    assert sorted(listed) == read_only
