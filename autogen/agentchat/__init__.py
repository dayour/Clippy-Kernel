# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from  https://github.com/microsoft/autogen are under the MIT License.
# SPDX-License-Identifier: MIT
from .agent import Agent, LLMAgent

# clippy kernel agent development team
from .agent_dev_team import (
    AgentDevTeam,
    AgentRole,
    SprintConfig,
    SprintPhase,
    UserStory,
    create_agent_dev_team,
    create_self_improving_team,
)
from .assistant_agent import AssistantAgent
from .chat import ChatResult, a_initiate_chats, initiate_chats

# Swarm agent (depends on ConversableAgent being defined first)
from .contrib.swarm_agent import (
    a_initiate_swarm_chat,
    a_run_swarm,
    run_swarm,
)
from .conversable_agent import ConversableAgent, UpdateSystemMessage, register_function
from .group import ContextVariables, ReplyResult
from .group.multi_agent_chat import (
    a_initiate_group_chat,
    a_run_group_chat,
    a_run_group_chat_iter,
    initiate_group_chat,
    run_group_chat,
    run_group_chat_iter,
)
from .groupchat import GroupChat, GroupChatManager
from .user_proxy_agent import UserProxyAgent
from .utils import gather_usage_summary

__all__ = [
    "Agent",
    "AssistantAgent",
    "ChatResult",
    "ContextVariables",
    "ConversableAgent",
    "GroupChat",
    "GroupChatManager",
    "LLMAgent",
    "ReplyResult",
    "UpdateSystemMessage",
    "UserProxyAgent",
    "a_initiate_chats",
    "a_initiate_group_chat",
    "a_initiate_swarm_chat",
    "a_run_group_chat",
    "a_run_group_chat_iter",
    "a_run_swarm",
    "gather_usage_summary",
    "initiate_chats",
    "initiate_group_chat",
    "register_function",
    "run_group_chat",
    "run_group_chat_iter",
    "run_swarm",
    # clippy kernel additions
    "AgentDevTeam",
    "create_agent_dev_team",
    "create_self_improving_team",
    "SprintConfig",
    "UserStory",
    "AgentRole",
    "SprintPhase",
]
