"""clippybot - Autonomous Software Engineering Framework.

This package provides the clippybot generative framework for autonomous
software engineering tasks, integrating clippy-agent capabilities with
multi-agent orchestration.
"""

from __future__ import annotations

import os
import sys
from functools import partial
from logging import WARNING, getLogger
from pathlib import Path

# Version and requirements
__version__ = "1.1.0"
PYTHON_MINIMUM_VERSION = (3, 11)

# Package directories
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
CONFIG_DIR = Path(os.getenv("clippybot_CONFIG_DIR", REPO_ROOT / "config"))
TOOLS_DIR = Path(os.getenv("clippybot_TOOLS_DIR", REPO_ROOT / "tools"))
TRAJECTORY_DIR = Path(os.getenv("clippybot_TRAJECTORY_DIR", REPO_ROOT / "trajectories"))

# Python version check
if sys.version_info < PYTHON_MINIMUM_VERSION:
    msg = (
        f"Python {sys.version_info.major}.{sys.version_info.minor} is not supported. "
        "clippybot requires Python 3.11 or higher."
    )
    raise RuntimeError(msg)


def get_agent_commit_hash() -> str:
    """Get the commit hash of the current clippybot commit."""
    try:
        from git import Repo
        repo = Repo(REPO_ROOT, search_parent_directories=False)
        return repo.head.object.hexsha
    except Exception:
        return "unavailable"


def get_agent_version_info() -> str:
    """Get version info string."""
    hash = get_agent_commit_hash()
    return f"This is clippybot version {__version__} ({hash=})."


# Lazy imports for modules
def __getattr__(name: str):
    """Lazy loading for module components."""
    # SWE module
    if name == "swe":
        from clippybot import swe as swe_module
        return swe_module
    if name == "clippyagent":
        from clippybot.swe.agent import clippyagent
        return clippyagent
    if name == "SWESwarmManager":
        from clippybot.swe.swarms import SWESwarmManager
        return SWESwarmManager
    if name == "SWESwarmConfig":
        from clippybot.swe.swarms import SWESwarmConfig
        return SWESwarmConfig

    # Copilot agents (Phase 3)
    if name == "CopilotConversableAgent":
        from clippybot.agentchat.copilot_agents import CopilotConversableAgent
        return CopilotConversableAgent
    if name == "CopilotAssistantAgent":
        from clippybot.agentchat.copilot_agents import CopilotAssistantAgent
        return CopilotAssistantAgent

    # LLM clients (Phase 2)
    if name == "CopilotLLMClient":
        from clippybot.llm_clients.copilot_client import CopilotLLMClient
        return CopilotLLMClient
    if name == "CopilotClientConfig":
        from clippybot.llm_clients.copilot_client import CopilotClientConfig
        return CopilotClientConfig

    # CS Builder agents (Phase 4)
    if name == "SecurityGovernanceAdvisorAgent":
        from clippybot.agents.cs_builder.security import SecurityGovernanceAdvisorAgent
        return SecurityGovernanceAdvisorAgent
    if name == "AgentScaffolderAgent":
        from clippybot.agents.cs_builder.scaffolder import AgentScaffolderAgent
        return AgentScaffolderAgent
    if name == "RequirementsPlannerAgent":
        from clippybot.agents.cs_builder.planner import RequirementsPlannerAgent
        return RequirementsPlannerAgent
    if name == "KnowledgeSourceIngestorAgent":
        from clippybot.agents.cs_builder.ingestor import KnowledgeSourceIngestorAgent
        return KnowledgeSourceIngestorAgent
    if name == "ActionsIntegratorAgent":
        from clippybot.agents.cs_builder.actions import ActionsIntegratorAgent
        return ActionsIntegratorAgent
    if name == "PublisherAgent":
        from clippybot.agents.cs_builder.publisher import PublisherAgent
        return PublisherAgent
    if name == "AnalyticsEvaluatorAgent":
        from clippybot.agents.cs_builder.analytics import AnalyticsEvaluatorAgent
        return AnalyticsEvaluatorAgent
    if name == "create_cs_builder_swarm":
        from clippybot.swarms.cs_builder import create_cs_builder_swarm
        return create_cs_builder_swarm
    if name == "run_build":
        from clippybot.swarms.cs_builder import run_build
        return run_build

    # Submodules
    if name == "agentchat":
        from clippybot import agentchat as agentchat_module
        return agentchat_module
    if name == "llm_clients":
        from clippybot import llm_clients as llm_clients_module
        return llm_clients_module
    if name == "agents":
        from clippybot import agents as agents_module
        return agents_module
    if name == "swarms":
        from clippybot import swarms as swarms_module
        return swarms_module
    if name == "tools":
        from clippybot import tools as tools_module
        return tools_module

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    "PACKAGE_DIR",
    "CONFIG_DIR",
    "TOOLS_DIR",
    "TRAJECTORY_DIR",
    "get_agent_commit_hash",
    "get_agent_version_info",
    # SWE components (lazy loaded)
    "clippyagent",
    "SWESwarmManager",
    "SWESwarmConfig",
    # Copilot agents (lazy loaded)
    "CopilotConversableAgent",
    "CopilotAssistantAgent",
    # LLM clients (lazy loaded)
    "CopilotLLMClient",
    "CopilotClientConfig",
    # CS Builder agents (lazy loaded)
    "SecurityGovernanceAdvisorAgent",
    "AgentScaffolderAgent",
    "RequirementsPlannerAgent",
    "KnowledgeSourceIngestorAgent",
    "ActionsIntegratorAgent",
    "PublisherAgent",
    "AnalyticsEvaluatorAgent",
    "create_cs_builder_swarm",
    "run_build",
]
