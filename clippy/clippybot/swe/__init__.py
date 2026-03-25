"""SWE (Software Engineering) module for clippybot.

This module provides autonomous software engineering capabilities including:
- clippyagent: An agent specialized for software engineering tasks
- SWE Tools: Bash, edit, and search tools for code manipulation
- SWE Environment: Execution environment for SWE tasks
- SWE Swarms: Multi-agent collaboration for complex SWE tasks
"""

from __future__ import annotations

from clippybot.swe.agent import clippyagent
from clippybot.swe.tools import (
    SWEToolConfig,
    get_swe_tools,
    SWETool,
    BashTool,
    EditTool,
    SearchTool,
)
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

__all__ = [
    # Agent
    "clippyagent",
    # Tools
    "SWEToolConfig",
    "get_swe_tools",
    "SWETool",
    "BashTool",
    "EditTool",
    "SearchTool",
    # Environment
    "SWEEnvironment",
    "SWEEnvironmentConfig",
    # Swarms
    "SWESwarmConfig",
    "SWESwarmManager",
    "create_code_review_swarm",
    "create_debug_swarm",
    "create_test_swarm",
]
