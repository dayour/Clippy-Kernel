# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
Clippy Kernel CLI Module

This module provides command-line interfaces for Clippy Kernel's
autonomous agent capabilities, including the SWE (Software Engineering) agent.
"""

from .clippy_swe_agent import ClippySWEAgent, ClippySWEConfig

__all__ = ["ClippySWEAgent", "ClippySWEConfig", "main"]


def main() -> None:
    """Entry point for the clippy-swe CLI command."""
    from .clippy_swe_cli import app

    app()
