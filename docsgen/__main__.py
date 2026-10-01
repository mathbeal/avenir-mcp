# SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
# SPDX-License-Identifier: MIT

"""Regenerate the generated parts of the documentation: `python -m docsgen`."""

from __future__ import annotations

from docsgen import pages

pages.write_all()
