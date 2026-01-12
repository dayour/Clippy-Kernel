# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
Clippy SWE Agent - Autonomous Software Engineering Agent

This module provides an autonomous agent capable of:
- Autonomous coding and code review
- Multi-agent orchestration for complex tasks
- Windows desktop application interaction
- Background task execution with observer mode
- Integration with development tools and IDEs
- Real-time collaboration and task management
"""

import asyncio
import json
import logging
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..agentchat import ConversableAgent, run_group_chat
from ..agentchat.group.patterns import AutoPattern
from ..import_utils import optional_import_block
from ..llm_config import LLMConfig
from ..mcp.clippy_kernel_tools import ClippyKernelToolkit, WebScrapingConfig
from ..tools import Toolkit

with optional_import_block():
    import psutil

logger = logging.getLogger(__name__)


class ClippySWEConfig(BaseModel):
    """Configuration for the Clippy SWE Agent."""

    # LLM Configuration
    llm_config_path: str = Field(default="OAI_CONFIG_LIST", description="Path to LLM configuration file")

    # Agent Behavior
    autonomous_mode: bool = Field(default=True, description="Enable fully autonomous operation")
    observer_mode: bool = Field(default=False, description="Enable visual observation and display of agent actions")
    background_mode: bool = Field(default=False, description="Run tasks in background without UI")
    max_iterations: int = Field(default=50, description="Maximum iterations for agent conversations")

    # Workspace Configuration
    workspace_path: Path = Field(default_factory=lambda: Path.cwd(), description="Working directory for agent")
    project_path: Path | None = Field(default=None, description="Project directory to work on")

    # Windows Integration
    enable_windows_automation: bool = Field(
        default=platform.system() == "Windows", description="Enable Windows desktop automation"
    )
    enable_app_interaction: bool = Field(default=True, description="Allow interaction with applications")

    # Tool Configuration
    enable_web_tools: bool = Field(default=True, description="Enable web scraping and API tools")
    enable_code_execution: bool = Field(default=True, description="Enable code execution capabilities")
    enable_file_operations: bool = Field(default=True, description="Enable file system operations")

    # Task Management
    task_history_path: Path = Field(
        default_factory=lambda: Path.cwd() / ".clippy_swe_history.json", description="Path to task history file"
    )
    save_conversation_history: bool = Field(default=True, description="Save conversation history")

    # Safety
    require_confirmation: bool = Field(default=False, description="Require user confirmation for critical operations")
    safe_mode: bool = Field(default=False, description="Enable additional safety checks")


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
    ) -> None:
        """Add a task to the history."""
        task = {
            "id": len(self.tasks) + 1,
            "type": task_type,
            "description": description,
            "status": status,
            "result": result,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.tasks.append(task)
        self._save_history()

    def get_recent_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent tasks."""
        return self.tasks[-limit:]


class ClippySWEAgent:
    """
    Autonomous Software Engineering Agent powered by Clippy Kernel.

    This agent provides a CLI interface similar to GitHub Copilot CLI but with
    enhanced capabilities including:
    - Autonomous coding and orchestration
    - Windows desktop automation
    - Multi-agent collaboration
    - Background task execution
    - Observer mode for visual feedback
    """

    def __init__(self, config: ClippySWEConfig | None = None):
        """Initialize the Clippy SWE Agent."""
        self.config = config or ClippySWEConfig()
        self.llm_config: LLMConfig | None = None
        self.task_history = TaskHistory(self.config.task_history_path)
        self.toolkit: Toolkit | None = None
        self.agents: dict[str, ConversableAgent] = {}

        logger.info("Initializing Clippy SWE Agent...")
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the agent and its components."""
        # Load LLM configuration
        try:
            self.llm_config = LLMConfig.from_json(path=self.config.llm_config_path)
            logger.info("LLM configuration loaded successfully")
        except FileNotFoundError:
            logger.warning(f"LLM config file not found: {self.config.llm_config_path}")
            logger.warning("Agent will operate in limited mode")

        # Initialize toolkit
        if self.config.enable_web_tools:
            self.toolkit = ClippyKernelToolkit(
                web_config=WebScrapingConfig(),
                enable_web_scraping=True,
                enable_database=False,
                enable_cloud=False,
                enable_development_tools=True,
            )
            logger.info(f"Toolkit initialized with {len(self.toolkit.tools)} tools")

        # Initialize specialized agents
        self._initialize_agents()

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
            error_msg = "Cannot execute task without LLM configuration"
            logger.error(error_msg)
            self.task_history.add_task(task_type, task_description, "failed", error=error_msg)
            return {"status": "failed", "error": error_msg}

        if self.config.observer_mode:
            print("\n" + "=" * 70)
            print("🔍 OBSERVER MODE: Autonomous Agent Execution")
            print("=" * 70)
            print(f"📋 Task: {task_description}")
            print(f"🏷️  Type: {task_type}")
            print(f"⚙️  Config: autonomous={self.config.autonomous_mode}, background={self.config.background_mode}")
            print("=" * 70 + "\n")

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
                print("🤖 Agent team assembled and starting collaboration...\n")

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

            if self.config.observer_mode:
                print("\n" + "=" * 70)
                print("✅ TASK COMPLETED SUCCESSFULLY")
                print("=" * 70)
                print(f"📊 Result: {task_result['result']}")
                print("=" * 70 + "\n")

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

            if self.config.observer_mode:
                print("\n" + "=" * 70)
                print("❌ TASK FAILED")
                print("=" * 70)
                print(f"🚫 Error: {str(e)}")
                print("=" * 70 + "\n")

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
            return {"status": "failed", "error": "Windows automation is disabled"}

        if platform.system() != "Windows":
            return {"status": "failed", "error": "Windows automation only available on Windows"}

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
                "autonomous_mode": self.config.autonomous_mode,
                "observer_mode": self.config.observer_mode,
            }

            # Task history
            recent_tasks = self.task_history.get_recent_tasks(5)
            status["recent_tasks"] = [
                {"id": task["id"], "type": task["type"], "status": task["status"], "timestamp": task["timestamp"]}
                for task in recent_tasks
            ]

            return status

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"status": "error", "error": str(e)}

    def list_recent_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent tasks from history."""
        return self.task_history.get_recent_tasks(limit)

    def get_task_by_id(self, task_id: int) -> dict[str, Any] | None:
        """Get a specific task by ID."""
        for task in self.task_history.tasks:
            if task["id"] == task_id:
                return task
        return None
