"""SWE (Software Engineering) module for clippybot.

This module provides autonomous software engineering capabilities including:
- clippyagent: An agent specialized for software engineering tasks
- SWE Tools: Bash, edit, and search tools for code manipulation
- SWE Environment: Execution environment for SWE tasks
- SWE Swarms: Multi-agent collaboration for complex SWE tasks
"""

from __future__ import annotations

from clippybot.swe.agent import clippyagent
from clippybot.swe.environment import (
    SWEEnvironment,
    SWEEnvironmentConfig,
)
from clippybot.swe.swarms import (
    SWESwarmConfig,
    SWESwarmManager,
    create_code_review_swarm,
    create_debug_swarm,
    create_test_swarm,
)
from clippybot.swe.tools import (
    BashTool,
    EditTool,
    SearchTool,
    SWETool,
    SWEToolConfig,
    get_swe_tools,
)

__all__ = [
    "BashTool",
    "EditTool",
    # Environment
    "SWEEnvironment",
    "SWEEnvironmentConfig",
    # Swarms
    "SWESwarmConfig",
    "SWESwarmManager",
    "SWETool",
    # Tools
    "SWEToolConfig",
    "SearchTool",
    # Agent
    "clippyagent",
    "create_code_review_swarm",
    "create_debug_swarm",
    "create_test_swarm",
    "get_swe_tools",
]
