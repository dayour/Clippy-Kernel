# Copyright (c) 2023 - 2025, clippy kernel development team
#
# SPDX-License-Identifier: Apache-2.0

"""
clippy kernel CLI module

This module provides command-line interfaces for clippy kernel's
autonomous agent capabilities, including the SWE (Software Engineering) agent.
"""

from .clippy_swe_agent import ClippySWEAgent, ClippySWEConfig

__all__ = ["ClippySWEAgent", "ClippySWEConfig", "main"]


def main() -> None:
    """Entry point for the clippy-swe CLI command."""
    from .clippy_swe_cli import app

    app()
