# Copyright (c) 2023 - 2025, clippy kernel development team
#
# SPDX-License-Identifier: Apache-2.0

"""
Clippy SWE Agent runtime for AG2-based software engineering workflows.

This module defines the configuration, task history, and main agent wrapper
used by the Clippy SWE CLI. The current implementation provides:
- AG2-based multi-agent task orchestration
- Shared Copilot-style config and session-state resolution
- Windows-aware task wrappers with OS guardrails
- Observer-mode console output and task history capture
- Optional toolkit metadata and experimental Copilot client initialization
"""

import json
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..agentchat import ConversableAgent, run_group_chat
from ..agentchat.group.patterns import AutoPattern
from ..import_utils import optional_import_block
from ..llm_config import LLMConfig
from ..mcp.clippy_kernel_tools import ClippyKernelToolkit, M365CopilotConfig, WebScrapingConfig, WorkIQConfig
from ..orchestration_metadata import build_semantic_envelope
from ..tools import Toolkit

with optional_import_block():
    import psutil

logger = logging.getLogger(__name__)


def _current_working_dir() -> Path:
    """Return the current working directory for default path resolution."""
    return Path.cwd()


def _copilot_config_dir() -> Path:
    """Return the shared Copilot configuration root."""
    return Path.home() / ".copilot"


def _clippy_state_dir() -> Path:
    """Return the shared clippy-kernel state directory under ~/.copilot."""
    return _copilot_config_dir() / "clippy-kernel"


def _prefer_legacy_workspace_path(legacy_path: Path, shared_path: Path) -> Path:
    """Prefer an existing workspace-local file, otherwise use the shared Copilot path."""
    return legacy_path if legacy_path.exists() else shared_path


def _default_llm_config_path() -> str:
    return str(_prefer_legacy_workspace_path(_current_working_dir() / "OAI_CONFIG_LIST", _clippy_state_dir() / "OAI_CONFIG_LIST"))


def _default_task_history_path() -> Path:
    return _prefer_legacy_workspace_path(
        _current_working_dir() / ".clippy_swe_history.json",
        _clippy_state_dir() / "task-history.json",
    )


def _default_interactive_session_path() -> Path:
    return _prefer_legacy_workspace_path(
        _current_working_dir() / ".clippy_session.json",
        _clippy_state_dir() / "interactive-session.json",
    )


def _default_skill_directories() -> list[Path]:
    return [_copilot_config_dir() / "skills"]


def _default_custom_agents_dir() -> Path:
    return _copilot_config_dir() / "agents"


def _default_mcp_config_path() -> Path:
    return _copilot_config_dir() / "mcp-config.json"


def _looks_like_mcp_server_config(value: Any) -> bool:
    return isinstance(value, dict) and any(
        key in value for key in ("command", "url", "transport", "args", "env", "headers", "type")
    )


def _load_mcp_servers_from_path(mcp_config_path: Path) -> dict[str, Any]:
    """Load MCP server definitions from a shared Copilot config file."""
    if not mcp_config_path.exists():
        return {}

    try:
        with open(mcp_config_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load MCP server config from {mcp_config_path}: {e}")
        return {}

    if not isinstance(data, dict):
        logger.warning(f"Ignoring MCP config at {mcp_config_path}: expected a JSON object at the top level")
        return {}

    for key in ("mcpServers", "servers"):
        servers = data.get(key)
        if isinstance(servers, dict):
            return {name: config for name, config in servers.items() if _looks_like_mcp_server_config(config)}

    if all(_looks_like_mcp_server_config(value) for value in data.values()):
        return data

    logger.warning(f"Ignoring MCP config at {mcp_config_path}: could not find a recognized MCP server map")
    return {}


def _observer_banner(title: str, details: list[str] | None = None) -> str:
    """Build a consistent observer-mode banner for logging."""
    lines = ["", "=" * 70, title, "=" * 70]
    if details:
        lines.extend(details)
        lines.append("=" * 70)
    lines.append("")
    return "\n".join(lines)


class ClippySWEConfig(BaseModel):
    """Configuration for the Clippy SWE Agent."""

    # LLM Configuration
    llm_config_path: str = Field(default_factory=_default_llm_config_path, description="Path to LLM configuration file")

    # Copilot SDK Configuration
    use_copilot_sdk: bool = Field(
        default=False,
        description="Initialize the experimental Copilot-style client path when configured",
    )
    github_token: str | None = Field(default=None, description="GitHub personal access token")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    google_api_key: str | None = Field(default=None, description="Google AI API key")
    copilot_model: str = Field(default="gpt-4", description="Preferred model for the optional Copilot-style client")
    copilot_provider: str = Field(
        default="openai",
        description="Preferred client provider: openai, anthropic, google, github_copilot",
    )
    enable_streaming: bool = Field(
        default=False,
        description="Enable streaming in the optional client path where supported",
    )
    context_window_size: int = Field(default=8192, description="Context window size for conversations")
    config_dir: Path = Field(default_factory=_copilot_config_dir, description="Shared GitHub Copilot configuration root")
    custom_agents_dir: Path = Field(
        default_factory=_default_custom_agents_dir,
        description="Shared directory for Copilot custom agent definitions",
    )
    skill_directories: list[Path] = Field(
        default_factory=_default_skill_directories,
        description="Directories used for shared Copilot skill discovery",
    )
    disabled_skills: list[str] = Field(default_factory=list, description="Names of Copilot skills to disable")
    mcp_config_path: Path = Field(
        default_factory=_default_mcp_config_path,
        description="Path to the shared Copilot MCP server configuration file",
    )
    mcp_servers: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional or overriding MCP server definitions for Copilot sessions",
    )

    # Agent Behavior
    autonomous_mode: bool = Field(default=True, description="Enable fully autonomous operation")
    observer_mode: bool = Field(default=False, description="Enable visual observation and display of agent actions")
    background_mode: bool = Field(
        default=False,
        description="Reduce task UI output; execution remains synchronous",
    )
    max_iterations: int = Field(default=50, description="Maximum iterations for agent conversations")

    # Workspace Configuration
    workspace_path: Path = Field(default_factory=lambda: Path.cwd(), description="Working directory for agent")
    project_path: Path | None = Field(default=None, description="Project directory to work on")

    # Windows Integration
    enable_windows_automation: bool = Field(
        default=platform.system() == "Windows",
        description="Enable Windows-specific task wrappers and OS guardrails",
    )
    enable_app_interaction: bool = Field(
        default=True,
        description="Add target application context to Windows task prompts",
    )

    # Tool Configuration
    enable_web_tools: bool = Field(default=True, description="Enable web scraping and API tools")
    enable_code_execution: bool = Field(default=True, description="Enable code execution capabilities")
    enable_file_operations: bool = Field(default=True, description="Enable file system operations")
    enable_workiq: bool = Field(
        default=False,
        description="Enable the WorkIQ-backed Microsoft 365 query tool in the runtime toolkit",
    )
    workiq_command: str = Field(default="npx", description="Command used to invoke WorkIQ")
    workiq_package: str = Field(default="@microsoft/workiq@latest", description="Package spec used with npx")
    workiq_tenant_id: str | None = Field(default=None, description="Optional default Entra tenant ID for WorkIQ")
    workiq_timeout: int = Field(default=120, description="Timeout in seconds for WorkIQ CLI calls")
    enable_m365_copilot: bool = Field(
        default=False,
        description="Enable Microsoft 365 Copilot SDK tools in the runtime toolkit",
    )
    m365_copilot_repo_path: Path | None = Field(
        default=None,
        description="Optional local Agents-M365Copilot repo path used when the SDK is not installed",
    )
    m365_copilot_tenant_id: str | None = Field(
        default=None,
        description="Optional default Entra tenant ID for Microsoft 365 Copilot SDK auth",
    )
    m365_copilot_client_id: str | None = Field(
        default=None,
        description="Optional client ID used for device-code Microsoft 365 Copilot auth",
    )
    m365_copilot_credential_mode: str = Field(
        default="default",
        description="Credential mode for Microsoft 365 Copilot SDK auth: default or device_code",
    )
    m365_copilot_default_user_id: str | None = Field(
        default=None,
        description="Optional default AI user identifier for user-scoped Microsoft 365 Copilot tools",
    )
    m365_copilot_scopes: list[str] = Field(
        default_factory=lambda: ["https://graph.microsoft.com/.default"],
        description="OAuth scopes used for Microsoft 365 Copilot SDK auth",
    )

    # Task Management
    task_history_path: Path = Field(
        default_factory=_default_task_history_path,
        description="Path to task history file",
    )
    interactive_session_path: Path = Field(
        default_factory=_default_interactive_session_path,
        description="Path to interactive session state",
    )
    save_conversation_history: bool = Field(default=True, description="Save conversation history")

    # Safety
    require_confirmation: bool = Field(default=False, description="Require user confirmation for critical operations")
    safe_mode: bool = Field(default=False, description="Enable additional safety checks")

    def resolve_mcp_servers(self) -> dict[str, Any]:
        """Resolve MCP servers from explicit config or the shared Copilot MCP config file."""
        if self.mcp_servers:
            return dict(self.mcp_servers)
        return _load_mcp_servers_from_path(self.mcp_config_path)

    def build_copilot_session_config(self) -> dict[str, Any]:
        """Build the shared Copilot session configuration used by future SDK-backed execution."""
        session_config: dict[str, Any] = {
            "working_directory": str(self.workspace_path),
            "config_dir": str(self.config_dir),
            "skill_directories": [str(path) for path in self.skill_directories],
            "disabled_skills": list(self.disabled_skills),
        }

        mcp_servers = self.resolve_mcp_servers()
        if mcp_servers:
            session_config["mcp_servers"] = mcp_servers

        return session_config


class TaskHistory:
    """Manages task execution history."""

    def __init__(self, history_path: Path):
        self.history_path = history_path
        self.tasks: list[dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load task history from file."""
        if self.history_path.exists():
            try:
                with open(self.history_path) as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                logger.info(f"Loaded {len(self.tasks)} tasks from history")
            except Exception as e:
                logger.warning(f"Failed to load task history: {e}")
                self.tasks = []

    def _save_history(self) -> None:
        """Save task history to file."""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_path, "w") as f:
                json.dump({"tasks": self.tasks, "last_updated": datetime.now().isoformat()}, f, indent=2)
            logger.info(f"Saved task history to {self.history_path}")
        except Exception as e:
            logger.error(f"Failed to save task history: {e}")

    def add_task(
        self,
        task_type: str,
        description: str,
        status: str,
        result: Any = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Add a task to the history."""
        task_metadata = dict(metadata or {})
        task = {
            "id": len(self.tasks) + 1,
            "type": task_type,
            "description": description,
            "status": status,
            "result": result,
            "metadata": task_metadata,
            "timestamp": datetime.now().isoformat(),
        }
        if error is not None:
            task["error"] = error

        task = task | build_semantic_envelope(
            schema_name="clippy-kernel.swe-agent.task-history.entry",
            kind="task-history-entry",
            workflow="task-history",
            primary_owner="task-coordinator",
            participant_roles=task_metadata.get("agents_used", []),
            focus_areas=["software-engineering", "task-tracking"],
            capabilities=["task-audit", "history", "orchestration"],
            tags=["clippy-swe", f"task-{task_type}", f"status-{status}"],
            attributes={"task_type": task_type, "status": status, "has_error": error is not None},
        )

        self.tasks.append(task)
        self._save_history()

    def get_recent_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent tasks."""
        return self.tasks[-limit:]


class ClippySWEAgent:
    """
    Autonomous Software Engineering Agent powered by clippy kernel.

    This agent provides the current Clippy SWE execution model:
    - AG2-based multi-agent orchestration for coding, research, and system tasks
    - Windows-aware system-task wrappers that add context and guardrails
    - Shared config resolution and task history management
    - Reduced-output observer and background flags for the synchronous CLI flow
    - Optional Copilot-style client initialization for future provider routing
    """

    def __init__(self, config: ClippySWEConfig | None = None):
        """Initialize the Clippy SWE Agent."""
        self.config = config or ClippySWEConfig()
        self.llm_config: LLMConfig | None = None
        self.copilot_session_config = self.config.build_copilot_session_config()
        self.task_history = TaskHistory(self.config.task_history_path)
        self.toolkit: Toolkit | None = None
        self.agents: dict[str, ConversableAgent] = {}
        self.copilot_sdk_client = None  # Will be initialized if use_copilot_sdk is True

        logger.info("Initializing Clippy SWE Agent...")
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the agent and its components."""
        logger.info(f"Using shared Copilot config root: {self.config.config_dir}")
        logger.info("Resolved LLM config path: %s", self.config.llm_config_path)
        logger.info("Resolved task history path: %s", self.config.task_history_path)
        logger.info("Resolved interactive session path: %s", self.config.interactive_session_path)
        logger.info("Resolved MCP config path: %s", self.config.mcp_config_path)
        if self.copilot_session_config.get("mcp_servers"):
            logger.info(
                "Loaded %s shared MCP server definitions from %s",
                len(self.copilot_session_config["mcp_servers"]),
                self.config.mcp_config_path,
            )

        # Load LLM configuration
        try:
            self.llm_config = LLMConfig.from_json(path=self.config.llm_config_path)
            logger.info("LLM configuration loaded successfully")
        except FileNotFoundError:
            logger.warning(f"LLM config file not found: {self.config.llm_config_path}")
            logger.warning("Agent will operate in limited mode")
        except Exception as e:
            logger.warning("Failed to load LLM configuration from %s: %s", self.config.llm_config_path, e)
            logger.warning("Agent will operate in limited mode")

        # Initialize Copilot SDK client if enabled
        if self.config.use_copilot_sdk:
            try:
                from .copilot_sdk_client import CopilotSDKClient, ModelProvider

                provider_map = {
                    "openai": ModelProvider.OPENAI,
                    "anthropic": ModelProvider.ANTHROPIC,
                    "google": ModelProvider.GOOGLE,
                    "github_copilot": ModelProvider.GITHUB_COPILOT,
                }

                self.copilot_sdk_client = CopilotSDKClient(
                    github_token=self.config.github_token,
                    openai_api_key=self.config.openai_api_key,
                    anthropic_api_key=self.config.anthropic_api_key,
                    google_api_key=self.config.google_api_key,
                    default_model=self.config.copilot_model,
                    default_provider=provider_map.get(self.config.copilot_provider, ModelProvider.OPENAI),
                )
                logger.info("Copilot SDK client initialized")
            except Exception as e:
                logger.warning(
                    "Failed to initialize Copilot SDK client for provider '%s': %s",
                    self.config.copilot_provider,
                    e,
                )

        # Initialize toolkit
        self.toolkit = ClippyKernelToolkit(
            web_config=WebScrapingConfig(),
            workiq_config=WorkIQConfig(
                command=self.config.workiq_command,
                package_spec=self.config.workiq_package,
                tenant_id=self.config.workiq_tenant_id,
                timeout=self.config.workiq_timeout,
            ),
            m365_copilot_config=M365CopilotConfig(
                repo_path=self.config.m365_copilot_repo_path,
                tenant_id=self.config.m365_copilot_tenant_id,
                client_id=self.config.m365_copilot_client_id,
                credential_mode=self.config.m365_copilot_credential_mode,
                scopes=list(self.config.m365_copilot_scopes),
                default_user_id=self.config.m365_copilot_default_user_id,
            ),
            enable_web_scraping=self.config.enable_web_tools,
            enable_database=False,
            enable_cloud=False,
            enable_workiq=self.config.enable_workiq,
            enable_m365_copilot=self.config.enable_m365_copilot,
            enable_development_tools=True,
        )
        logger.info(f"Toolkit initialized with {len(self.toolkit.tools)} tools")

        # Initialize specialized agents
        self._initialize_agents()
        self._register_toolkit_with_agents()

        logger.info("Clippy SWE Agent initialized successfully")

    def _initialize_agents(self) -> None:
        """Initialize specialized agents for different tasks."""
        if not self.llm_config:
            logger.warning("Cannot initialize agents without LLM configuration")
            return

        # Software Engineer Agent
        self.agents["engineer"] = ConversableAgent(
            name="software_engineer",
            system_message="""You are an expert software engineer with deep knowledge of:
            - Multiple programming languages (Python, JavaScript, Java, C++, Go, Rust, etc.)
            - Software architecture and design patterns
            - Code optimization and performance tuning
            - Testing strategies and quality assurance
            - DevOps and CI/CD practices
            
            You can autonomously:
            - Write, review, and refactor code
            - Design system architectures
            - Debug complex issues
            - Implement new features
            - Optimize existing code
            
            You work efficiently and provide clear, concise solutions.""",
            llm_config=self.llm_config,
        )

        # System Administrator Agent
        self.agents["sysadmin"] = ConversableAgent(
            name="system_administrator",
            system_message="""You are an expert system administrator with skills in:
            - Windows, Linux, and macOS system administration
            - Process management and automation
            - File system operations
            - Network configuration
            - Application deployment and management
            
            You can autonomously:
            - Execute system commands
            - Manage processes and services
            - Configure applications
            - Monitor system resources
            - Automate system tasks
            
            You prioritize system stability and security.""",
            llm_config=self.llm_config,
        )

        # Research & Analysis Agent
        self.agents["researcher"] = ConversableAgent(
            name="researcher",
            system_message="""You are an expert researcher and analyst who:
            - Investigates technical problems thoroughly
            - Searches for documentation and best practices
            - Analyzes codebases and identifies patterns
            - Recommends optimal solutions
            - Stays updated with latest technologies
            
            You can autonomously:
            - Research technical topics
            - Analyze code and systems
            - Compare alternative solutions
            - Provide detailed recommendations
            - Document findings clearly
            
            You are thorough and evidence-based in your analysis.""",
            llm_config=self.llm_config,
        )

        # Task Coordinator Agent
        self.agents["coordinator"] = ConversableAgent(
            name="task_coordinator",
            system_message="""You are an expert task coordinator who:
            - Breaks down complex tasks into manageable steps
            - Delegates work to specialized agents
            - Monitors progress and ensures completion
            - Handles exceptions and errors
            - Synthesizes results from multiple agents
            
            When a task is complete, output: TASK_COMPLETE!
            
            You orchestrate efficiently and ensure quality results.""",
            is_termination_msg=lambda x: "TASK_COMPLETE!" in (x.get("content", "") or "").upper(),
            llm_config=self.llm_config,
        )

        logger.info(f"Initialized {len(self.agents)} specialized agents")

    def _register_toolkit_with_agents(self) -> None:
        """Register toolkit tools onto all initialized agents."""
        if not self.toolkit or not self.agents:
            return

        for agent in self.agents.values():
            self.toolkit.register_for_llm(agent)
            self.toolkit.register_for_execution(agent)

        tool_count = len(self.toolkit.tools) if hasattr(self.toolkit, "tools") else 0
        logger.info("Registered %s toolkit tools across %s agents", tool_count, len(self.agents))

    def _task_metadata(
        self,
        *,
        schema_name: str,
        task_type: str,
        status: str,
        workflow: str,
        agents_used: list[str] | None = None,
        capabilities: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
        kind: str = "task-result",
    ) -> dict[str, Any]:
        """Build semantic metadata for SWE orchestration payloads."""
        semantic_attributes = {
            "task_type": task_type,
            "status": status,
            "workspace_path": str(self.config.workspace_path),
        }
        if self.config.project_path:
            semantic_attributes["project_path"] = str(self.config.project_path)
        if attributes:
            semantic_attributes.update(attributes)

        return build_semantic_envelope(
            schema_name=schema_name,
            kind=kind,
            workflow=workflow,
            primary_owner="task-coordinator",
            participant_roles=agents_used or [],
            focus_areas=["delivery", "automation", "coordination"],
            capabilities=capabilities or ["autonomous-execution", "multi-agent-collaboration"],
            tags=["clippy-swe", f"task-{task_type}", f"status-{status}"],
            attributes=semantic_attributes,
        )

    def execute_task(
        self, task_description: str, task_type: str = "general", context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a task using the autonomous agent system.

        Args:
            task_description: Description of the task to execute
            task_type: Type of task (general, coding, system, research, etc.)
            context: Additional context for the task

        Returns:
            Dictionary containing task results and metadata
        """
        logger.info(f"Executing task: {task_description}")

        if not self.llm_config:
            error_msg = (
                "Cannot execute task without LLM configuration. "
                f"Create or point llm_config_path to a valid OAI_CONFIG_LIST file at {self.config.llm_config_path}."
            )
            logger.error(error_msg)
            self.task_history.add_task(task_type, task_description, "failed", error=error_msg)
            return {
                "status": "failed",
                "task_description": task_description,
                "task_type": task_type,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
            } | self._task_metadata(
                schema_name="clippy-kernel.swe-agent.task-result",
                task_type=task_type,
                status="failed",
                workflow="task-execution",
                capabilities=["task-validation", "history", "orchestration"],
                attributes={"llm_configured": False},
                kind="task-error",
            )

        if self.config.observer_mode:
            logger.info(
                _observer_banner(
                    "OBSERVER MODE: Autonomous Agent Execution",
                    [
                        f"Task: {task_description}",
                        f"Type: {task_type}",
                        f"Config: autonomous={self.config.autonomous_mode}, background={self.config.background_mode}",
                    ],
                )
            )

        try:
            # Select appropriate agents based on task type
            selected_agents = self._select_agents_for_task(task_type)

            # Add context to task description
            full_task = self._prepare_task_message(task_description, context)

            # Create agent pattern for collaboration
            agent_pattern = AutoPattern(
                agents=selected_agents,
                initial_agent=selected_agents[0],
                group_manager_args={"name": "task_manager", "llm_config": self.llm_config},
            )

            # Execute task with agents
            if self.config.observer_mode:
                logger.info("Agent team assembled and starting collaboration...")

            result = run_group_chat(pattern=agent_pattern, messages=full_task, max_rounds=self.config.max_iterations)

            # Process results
            task_result = {
                "status": "completed",
                "task_description": task_description,
                "task_type": task_type,
                "result": result.summary if hasattr(result, "summary") else str(result),
                "chat_history": result.chat_history if hasattr(result, "chat_history") else [],
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "agents_used": [agent.name for agent in selected_agents],
                    "iterations": len(result.chat_history) if hasattr(result, "chat_history") else 0,
                },
            }
            task_result = task_result | self._task_metadata(
                schema_name="clippy-kernel.swe-agent.task-result",
                task_type=task_type,
                status="completed",
                workflow="task-execution",
                agents_used=task_result["metadata"]["agents_used"],
                attributes={"iterations": task_result["metadata"]["iterations"]},
            )

            if self.config.observer_mode:
                logger.info(
                    _observer_banner(
                        "TASK COMPLETED SUCCESSFULLY",
                        [f"Result: {task_result['result']}"],
                    )
                )

            # Save to history
            if self.config.save_conversation_history:
                self.task_history.add_task(
                    task_type=task_type,
                    description=task_description,
                    status="completed",
                    result=task_result["result"],
                    metadata=task_result["metadata"],
                )

            return task_result

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            error_result = {
                "status": "failed",
                "task_description": task_description,
                "task_type": task_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            error_result = error_result | self._task_metadata(
                schema_name="clippy-kernel.swe-agent.task-result",
                task_type=task_type,
                status="failed",
                workflow="task-execution",
                capabilities=["incident-reporting", "history", "orchestration"],
                attributes={"exception_type": type(e).__name__},
                kind="task-error",
            )

            if self.config.observer_mode:
                logger.info(_observer_banner("TASK FAILED", [f"Error: {str(e)}"]))

            self.task_history.add_task(task_type, task_description, "failed", error=str(e))
            return error_result

    def _select_agents_for_task(self, task_type: str) -> list[ConversableAgent]:
        """Select appropriate agents based on task type."""
        # Define agent selection strategy
        task_agent_mapping = {
            "coding": ["engineer", "researcher", "coordinator"],
            "system": ["sysadmin", "engineer", "coordinator"],
            "research": ["researcher", "engineer", "coordinator"],
            "general": ["coordinator", "engineer", "researcher"],
            "debug": ["engineer", "researcher", "coordinator"],
            "deploy": ["sysadmin", "engineer", "coordinator"],
            "test": ["engineer", "coordinator"],
            "review": ["engineer", "researcher", "coordinator"],
        }

        # Get agent names for task type
        agent_names = task_agent_mapping.get(task_type, task_agent_mapping["general"])

        # Return agent instances
        return [self.agents[name] for name in agent_names if name in self.agents]

    def _prepare_task_message(self, task_description: str, context: dict[str, Any] | None = None) -> str:
        """Prepare the task message with context."""
        message_parts = [f"**Task**: {task_description}"]

        if context:
            message_parts.append("\n**Context**:")
            for key, value in context.items():
                message_parts.append(f"- {key}: {value}")

        if self.config.workspace_path:
            message_parts.append(f"\n**Workspace**: {self.config.workspace_path}")

        if self.config.project_path:
            message_parts.append(f"**Project Path**: {self.config.project_path}")

        # Add system information
        message_parts.append(f"\n**System**: {platform.system()} {platform.release()}")
        message_parts.append(f"**Python**: {platform.python_version()}")

        # Add available tools information
        if self.toolkit:
            message_parts.append(f"\n**Available Tools**: {len(self.toolkit.tools)} tools available")
            if self.config.enable_workiq:
                message_parts.append(
                    "- WorkIQ is available for Microsoft 365 questions about emails, meetings, documents, Teams, and people."
                )
            if self.config.enable_m365_copilot:
                message_parts.append(
                    "- Microsoft 365 Copilot SDK tools are available for retrieval, reporting, users, interactions, admin settings, and online meetings."
                )

        message_parts.append("\n**Instructions**:")
        message_parts.append("- Work autonomously to complete the task")
        message_parts.append("- Coordinate with team members efficiently")
        message_parts.append("- Provide clear, actionable results")
        message_parts.append("- When task is complete, the coordinator should output 'TASK_COMPLETE!'")

        return "\n".join(message_parts)

    def execute_windows_task(self, task_description: str, app_name: str | None = None) -> dict[str, Any]:
        """
        Execute a Windows-specific task with optional application interaction.

        Args:
            task_description: Description of the Windows task
            app_name: Name of the application to interact with (optional)

        Returns:
            Dictionary containing task results
        """
        if not self.config.enable_windows_automation:
            return {"status": "failed", "error": "Windows automation is disabled"} | self._task_metadata(
                schema_name="clippy-kernel.swe-agent.windows-task",
                task_type="system",
                status="failed",
                workflow="windows-automation",
                capabilities=["windows-automation", "guardrails"],
                kind="task-error",
            )

        if platform.system() != "Windows":
            return {"status": "failed", "error": "Windows automation only available on Windows"} | self._task_metadata(
                schema_name="clippy-kernel.swe-agent.windows-task",
                task_type="system",
                status="failed",
                workflow="windows-automation",
                capabilities=["windows-automation", "guardrails"],
                kind="task-error",
            )

        context = {"platform": "Windows", "app_interaction": self.config.enable_app_interaction}

        if app_name:
            context["target_application"] = app_name
            context["task_note"] = f"Focus on interacting with {app_name}"

        return self.execute_task(task_description, task_type="system", context=context)

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status and resource usage."""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                },
                "python": {"version": platform.python_version(), "implementation": platform.python_implementation()},
                "resources": {},
            }

            # Add resource information if psutil is available
            try:
                status["resources"] = {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "cpu_count": psutil.cpu_count(),
                    "memory": psutil.virtual_memory()._asdict(),
                    "disk": psutil.disk_usage("/")._asdict(),
                }
            except Exception:
                pass

            # Agent status
            status["agent"] = {
                "initialized": len(self.agents) > 0,
                "agent_count": len(self.agents),
                "llm_configured": self.llm_config is not None,
                "toolkit_enabled": self.toolkit is not None,
                "tool_count": len(self.toolkit.tools) if self.toolkit else 0,
                "autonomous_mode": self.config.autonomous_mode,
                "observer_mode": self.config.observer_mode,
                "workiq_enabled": self.config.enable_workiq,
                "m365_copilot_enabled": self.config.enable_m365_copilot,
            }
            status["copilot"] = {
                "config_dir": str(self.config.config_dir),
                "custom_agents_dir": str(self.config.custom_agents_dir),
                "skill_directories": [str(path) for path in self.config.skill_directories],
                "mcp_config_path": str(self.config.mcp_config_path),
                "resolved_mcp_servers": sorted(self.copilot_session_config.get("mcp_servers", {}).keys()),
                "workiq_command": self.config.workiq_command if self.config.enable_workiq else None,
                "workiq_tenant_id": self.config.workiq_tenant_id,
                "m365_copilot_repo_path": (
                    str(self.config.m365_copilot_repo_path) if self.config.m365_copilot_repo_path else None
                ),
                "m365_copilot_tenant_id": self.config.m365_copilot_tenant_id,
                "m365_copilot_credential_mode": (
                    self.config.m365_copilot_credential_mode if self.config.enable_m365_copilot else None
                ),
                "m365_copilot_default_user_id": self.config.m365_copilot_default_user_id,
            }

            # Task history
            recent_tasks = self.task_history.get_recent_tasks(5)
            status["recent_tasks"] = [
                {"id": task["id"], "type": task["type"], "status": task["status"], "timestamp": task["timestamp"]}
                for task in recent_tasks
            ]

            return status | self._task_metadata(
                schema_name="clippy-kernel.swe-agent.system-status",
                task_type="system",
                status="ready",
                workflow="system-status",
                agents_used=list(self.agents.keys()),
                capabilities=["diagnostics", "status-reporting", "orchestration"],
                attributes={"recent_task_count": len(status["recent_tasks"])},
                kind="status-report",
            )

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"status": "error", "error": str(e)} | self._task_metadata(
                schema_name="clippy-kernel.swe-agent.system-status",
                task_type="system",
                status="error",
                workflow="system-status",
                capabilities=["diagnostics", "status-reporting"],
                attributes={"exception_type": type(e).__name__},
                kind="task-error",
            )

    def list_recent_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent tasks from history."""
        return self.task_history.get_recent_tasks(limit)

    def get_task_by_id(self, task_id: int) -> dict[str, Any] | None:
        """Get a specific task by ID."""
        for task in self.task_history.tasks:
            if task["id"] == task_id:
                return task
        return None
