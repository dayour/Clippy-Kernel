# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
Clippy SWE CLI - Command-line interface for autonomous SWE agent

This module provides a rich CLI interface for the Clippy SWE Agent,
similar to GitHub Copilot CLI but with enhanced autonomous capabilities.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

from ..import_utils import optional_import_block, require_optional_import

with optional_import_block():
    import typer
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.panel import Panel
    from rich.table import Table

from .clippy_swe_agent import ClippySWEAgent, ClippySWEConfig

# Initialize Typer app
try:
    require_optional_import("typer", "mcp-proxy-gen")
    app = typer.Typer(
        name="clippy-swe",
        help="Clippy SWE - Autonomous Software Engineering Agent",
        add_completion=True,
        rich_markup_mode="rich",
    )
    console = Console()
except ImportError:
    # Fallback if typer is not available
    app = None
    console = None

    def fallback_main():
        """Fallback main function when typer is not available."""
        print("Error: The clippy-swe command requires additional dependencies.")
        print("Install with: pip install -e '.[mcp-proxy-gen]'")
        sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging with rich formatting."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)] if console else [logging.StreamHandler()],
    )


@app.command()
def task(
    description: str = typer.Argument(..., help="Task description for the agent to execute"),
    task_type: str = typer.Option("general", "--type", "-t", help="Task type (general, coding, system, research)"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to custom configuration file"),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    project: Optional[Path] = typer.Option(None, "--project", "-p", help="Project directory"),
    observer: bool = typer.Option(False, "--observer", "-o", help="Enable observer mode (visual feedback)"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background mode"),
    autonomous: bool = typer.Option(True, "--autonomous/--interactive", help="Run autonomously or interactively"),
    max_iterations: int = typer.Option(50, "--max-iterations", "-i", help="Maximum iterations"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Execute a task using the autonomous SWE agent.

    Examples:
        clippy-swe task "Create a Flask REST API with user authentication"
        clippy-swe task "Fix the bug in auth.py" --type coding --project ./myapp
        clippy-swe task "Research best practices for React hooks" --type research
    """
    setup_logging(verbose)

    try:
        # Load configuration
        agent_config = ClippySWEConfig(
            autonomous_mode=autonomous,
            observer_mode=observer,
            background_mode=background,
            max_iterations=max_iterations,
        )

        if workspace:
            agent_config.workspace_path = workspace
        if project:
            agent_config.project_path = project

        if config:
            # Load custom config if provided
            with open(config) as f:
                custom_config = json.load(f)
                agent_config = ClippySWEConfig(**custom_config)

        # Display task information
        if not background:
            console.print(
                Panel.fit(
                    f"[bold cyan]Task:[/bold cyan] {description}\n"
                    f"[bold green]Type:[/bold green] {task_type}\n"
                    f"[bold yellow]Mode:[/bold yellow] {'Autonomous' if autonomous else 'Interactive'}",
                    title="🤖 Clippy SWE Agent",
                    border_style="blue",
                )
            )

        # Initialize and execute
        agent = ClippySWEAgent(config=agent_config)
        result = agent.execute_task(description, task_type=task_type)

        # Display results
        if not background:
            if result["status"] == "completed":
                console.print("\n[bold green]✅ Task Completed Successfully![/bold green]")
                console.print(Panel(result["result"], title="Result", border_style="green"))
            else:
                console.print("\n[bold red]❌ Task Failed[/bold red]")
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Task interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def windows(
    description: str = typer.Argument(..., help="Windows task description"),
    app_name: Optional[str] = typer.Option(None, "--app", "-a", help="Application name to interact with"),
    observer: bool = typer.Option(True, "--observer/--no-observer", help="Enable observer mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Execute Windows-specific tasks with application interaction.

    Examples:
        clippy-swe windows "Open Visual Studio Code and create a new Python project"
        clippy-swe windows "Take a screenshot and save to Desktop" --app "Snipping Tool"
        clippy-swe windows "Monitor CPU usage and alert if >80%"
    """
    setup_logging(verbose)

    try:
        agent_config = ClippySWEConfig(
            observer_mode=observer, enable_windows_automation=True, enable_app_interaction=True
        )

        agent = ClippySWEAgent(config=agent_config)

        console.print(
            Panel.fit(
                f"[bold cyan]Windows Task:[/bold cyan] {description}\n"
                + (f"[bold yellow]Target App:[/bold yellow] {app_name}\n" if app_name else ""),
                title="🪟 Windows Automation",
                border_style="blue",
            )
        )

        result = agent.execute_windows_task(description, app_name=app_name)

        if result["status"] == "completed":
            console.print("\n[bold green]✅ Windows Task Completed![/bold green]")
            console.print(Panel(result["result"], title="Result", border_style="green"))
        else:
            console.print("\n[bold red]❌ Task Failed[/bold red]")
            console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")

    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed system information"),
) -> None:
    """
    Display current system status and agent information.
    """
    setup_logging(verbose)

    try:
        agent_config = ClippySWEConfig()
        agent = ClippySWEAgent(config=agent_config)

        status_info = agent.get_system_status()

        # Create status table
        table = Table(title="🤖 Clippy SWE Agent Status", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")

        # Platform info
        platform_info = status_info.get("platform", {})
        table.add_row("System", f"{platform_info.get('system')} {platform_info.get('release')}")
        table.add_row("Python", status_info.get("python", {}).get("version"))

        # Agent info
        agent_info = status_info.get("agent", {})
        table.add_row("Agent Initialized", "✅" if agent_info.get("initialized") else "❌")
        table.add_row("LLM Configured", "✅" if agent_info.get("llm_configured") else "❌")
        table.add_row("Autonomous Mode", "✅" if agent_info.get("autonomous_mode") else "❌")
        table.add_row("Agent Count", str(agent_info.get("agent_count", 0)))

        # Resource info if available
        resources = status_info.get("resources", {})
        if resources:
            table.add_row("CPU Usage", f"{resources.get('cpu_percent', 0):.1f}%")
            memory = resources.get("memory", {})
            if memory:
                memory_percent = memory.get("percent", 0)
                table.add_row("Memory Usage", f"{memory_percent:.1f}%")

        console.print(table)

        # Recent tasks
        recent_tasks = status_info.get("recent_tasks", [])
        if recent_tasks and verbose:
            console.print("\n[bold]Recent Tasks:[/bold]")
            for task in recent_tasks:
                status_emoji = "✅" if task["status"] == "completed" else "❌"
                console.print(f"  {status_emoji} [{task['type']}] Task #{task['id']} - {task['status']}")

    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent tasks to show"),
    task_id: Optional[int] = typer.Option(None, "--id", help="Show specific task by ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed task information"),
) -> None:
    """
    Display task execution history.
    """
    setup_logging(verbose)

    try:
        agent_config = ClippySWEConfig()
        agent = ClippySWEAgent(config=agent_config)

        if task_id:
            # Show specific task
            task = agent.get_task_by_id(task_id)
            if task:
                console.print(Panel.fit(f"[bold cyan]Task #{task['id']}[/bold cyan]", border_style="cyan"))
                console.print(f"[bold]Type:[/bold] {task['type']}")
                console.print(f"[bold]Status:[/bold] {task['status']}")
                console.print(f"[bold]Description:[/bold] {task['description']}")
                console.print(f"[bold]Timestamp:[/bold] {task['timestamp']}")

                if verbose and task.get("result"):
                    console.print("\n[bold]Result:[/bold]")
                    console.print(task["result"])

                if task.get("metadata"):
                    console.print("\n[bold]Metadata:[/bold]")
                    console.print(json.dumps(task["metadata"], indent=2))
            else:
                console.print(f"[red]Task #{task_id} not found[/red]")
        else:
            # Show recent tasks
            tasks = agent.list_recent_tasks(limit)

            if not tasks:
                console.print("[yellow]No tasks in history[/yellow]")
                return

            table = Table(title=f"📜 Recent Tasks (Last {limit})", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Type", style="blue")
            table.add_column("Status", style="green")
            table.add_column("Description", style="white")
            table.add_column("Timestamp", style="yellow")

            for task in tasks:
                status_emoji = "✅" if task["status"] == "completed" else "❌"
                description = task["description"][:50] + "..." if len(task["description"]) > 50 else task["description"]
                table.add_row(
                    str(task["id"]), task["type"], f"{status_emoji} {task['status']}", description, task["timestamp"]
                )

            console.print(table)

    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def init(
    workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Workspace directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Force initialization even if config exists"),
) -> None:
    """
    Initialize Clippy SWE Agent configuration in the workspace.
    """
    try:
        config_path = workspace / ".clippy_swe_config.json"

        if config_path.exists() and not force:
            console.print(f"[yellow]⚠️  Configuration already exists at {config_path}[/yellow]")
            console.print("[yellow]Use --force to overwrite[/yellow]")
            return

        # Create default configuration
        default_config = ClippySWEConfig(workspace_path=workspace)

        config_data = default_config.model_dump()
        # Convert Path objects to strings for JSON serialization
        config_data["workspace_path"] = str(config_data["workspace_path"])
        config_data["task_history_path"] = str(config_data["task_history_path"])
        if config_data["project_path"]:
            config_data["project_path"] = str(config_data["project_path"])

        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)

        console.print(f"[green]✅ Configuration initialized at {config_path}[/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  1. Edit {config_path} to customize settings")
        console.print(f"  2. Create OAI_CONFIG_LIST file with your API keys")
        console.print(f"  3. Run: clippy-swe task 'Your task description'")

    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@app.command()
def version() -> None:
    """Display version information."""
    try:
        from ..version import __version__

        console.print(f"[bold cyan]Clippy SWE Agent[/bold cyan] version [bold green]{__version__}[/bold green]")
        console.print("[dim]Part of Clippy Kernel - Advanced R&D Fork of AG2[/dim]")
    except Exception:
        console.print("[bold cyan]Clippy SWE Agent[/bold cyan] (development version)")


def main() -> None:
    """Main entry point for CLI."""
    if app is None:
        fallback_main()
    else:
        app()


if __name__ == "__main__":
    main()
