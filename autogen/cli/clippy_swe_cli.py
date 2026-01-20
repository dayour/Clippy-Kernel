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
def interactive(
    session_file: Optional[Path] = typer.Option(None, "--session", "-s", help="Session file to save/load"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to custom configuration file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Start interactive conversational mode (like GitHub Copilot CLI).
    
    Features:
    - Natural language prompts
    - File attachments with @ prefix
    - Shell command execution with ! prefix
    - Slash commands (/model, /clear, /usage, etc.)
    - Session persistence
    
    Examples:
        clippy-swe interactive
        clippy-swe interactive --session my-session.json
    """
    setup_logging(verbose)
    
    try:
        from .interactive_mode import InteractiveSession
        
        # Load configuration
        agent_config = ClippySWEConfig()
        if config:
            with open(config) as f:
                custom_config = json.load(f)
                agent_config = ClippySWEConfig(**custom_config)
        
        # Create agent
        agent = ClippySWEAgent(config=agent_config)
        
        # Start interactive session
        session = InteractiveSession(agent, session_file=session_file)
        session.run()
        
    except ImportError:
        console.print("[red]Error: Interactive mode requires rich library[/red]")
        console.print("Install with: pip install -e '.[mcp-proxy-gen]'")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def resolve_issue(
    repository: str = typer.Argument(..., help="GitHub repository (owner/repo)"),
    issue_number: int = typer.Argument(..., help="Issue number to resolve"),
    create_pr: bool = typer.Option(True, "--create-pr/--no-pr", help="Create pull request"),
    github_token: Optional[str] = typer.Option(None, "--token", "-t", help="GitHub personal access token"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Automatically resolve a GitHub issue (SWE-agent style).
    
    This command will:
    1. Clone the repository
    2. Analyze the issue and codebase
    3. Generate a solution
    4. Run tests to validate
    5. Create a PR (if --create-pr)
    
    Examples:
        clippy-swe resolve-issue owner/repo 123
        clippy-swe resolve-issue owner/repo 456 --token ghp_xxx --create-pr
    """
    setup_logging(verbose)
    
    try:
        from .github_integration import GitHubIntegration
        
        console.print(
            Panel.fit(
                f"[bold cyan]Resolving Issue[/bold cyan]\n"
                f"[bold green]Repository:[/bold green] {repository}\n"
                f"[bold yellow]Issue:[/bold yellow] #{issue_number}\n"
                f"[bold blue]Create PR:[/bold blue] {create_pr}",
                title="🔧 GitHub Integration",
                border_style="blue",
            )
        )
        
        # Create agent
        agent_config = ClippySWEConfig(observer_mode=True)
        agent = ClippySWEAgent(config=agent_config)
        
        # Initialize GitHub integration
        gh_integration = GitHubIntegration(agent, github_token=github_token)
        
        # Resolve issue
        result = gh_integration.resolve_issue(repository, issue_number, create_pr=create_pr)
        
        # Display results
        if result.success:
            console.print("\n[bold green]✅ Issue Resolved Successfully![/bold green]")
            if result.patch_file:
                console.print(f"[cyan]Patch file: {result.patch_file}[/cyan]")
            if result.changed_files:
                console.print(f"[cyan]Changed files: {', '.join(result.changed_files)}[/cyan]")
            console.print(f"[cyan]Tests passed: {result.tests_passed}[/cyan]")
        else:
            console.print("\n[bold red]❌ Issue Resolution Failed[/bold red]")
            if result.error_message:
                console.print(f"[red]Error: {result.error_message}[/red]")
        
        # Cleanup
        gh_integration.cleanup()
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def generate_ppt(
    content_sources: list[str] = typer.Argument(..., help="Content sources (files or text)"),
    output: Path = typer.Option("presentation.pptx", "--output", "-o", help="Output PowerPoint file"),
    title: str = typer.Option("Presentation", "--title", "-t", help="Presentation title"),
    subtitle: Optional[str] = typer.Option(None, "--subtitle", "-s", help="Presentation subtitle"),
    generate_images: bool = typer.Option(True, "--generate-images/--no-images", help="Generate images with Flux 2"),
    flux_api_key: Optional[str] = typer.Option(None, "--flux-key", help="Flux 2 API key"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Generate PowerPoint presentation from content, images, docs, etc.
    
    Uses Flux 2 for image generation and multi-agent analysis for content.
    
    Examples:
        clippy-swe generate-ppt "content1.txt" "content2.md" --title "My Presentation"
        clippy-swe generate-ppt document.pdf --generate-images --flux-key YOUR_KEY
    """
    setup_logging(verbose)
    
    try:
        from .document_processor import DocumentProcessor, PowerPointSpec
        
        console.print(
            Panel.fit(
                f"[bold cyan]Generating PowerPoint[/bold cyan]\n"
                f"[bold green]Title:[/bold green] {title}\n"
                f"[bold yellow]Sources:[/bold yellow] {len(content_sources)}\n"
                f"[bold blue]Images:[/bold blue] {'Enabled' if generate_images else 'Disabled'}",
                title="📊 PowerPoint Generation",
                border_style="blue",
            )
        )
        
        # Create agent
        agent_config = ClippySWEConfig()
        agent = ClippySWEAgent(config=agent_config)
        
        # Initialize document processor
        processor = DocumentProcessor(agent, flux_api_key=flux_api_key)
        
        # Convert content sources to Paths where applicable
        sources = [Path(s) if Path(s).exists() else s for s in content_sources]
        
        # Create spec
        spec = PowerPointSpec(title=title, subtitle=subtitle)
        
        # Generate PowerPoint
        result = processor.generate_powerpoint(sources, output, spec, generate_images)
        
        if result["success"]:
            console.print("\n[bold green]✅ PowerPoint Generated Successfully![/bold green]")
            console.print(f"[cyan]Output: {result['output_path']}[/cyan]")
            console.print(f"[cyan]Slides: {result['slide_count']}[/cyan]")
            console.print(f"[cyan]Images: {result['images_generated']}[/cyan]")
        else:
            console.print(f"\n[bold red]❌ Generation Failed: {result.get('error')}[/bold red]")
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def analyze_doc(
    file_path: Path = typer.Argument(..., help="Document to analyze"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save analysis to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Analyze documents (PDF, Word, Excel, PowerPoint, etc.).
    
    Extracts content, provides summary, key points, and insights.
    
    Examples:
        clippy-swe analyze-doc document.pdf
        clippy-swe analyze-doc report.docx --output analysis.txt
    """
    setup_logging(verbose)
    
    try:
        from .document_processor import DocumentProcessor
        
        if not file_path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            sys.exit(1)
        
        console.print(f"[cyan]Analyzing document: {file_path}[/cyan]")
        
        agent_config = ClippySWEConfig()
        agent = ClippySWEAgent(config=agent_config)
        processor = DocumentProcessor(agent)
        
        result = processor.analyze_document(file_path)
        
        # Display results
        console.print(Panel.fit(result.summary, title="📄 Summary", border_style="green"))
        
        if result.key_points:
            console.print("\n[bold]Key Points:[/bold]")
            for point in result.key_points:
                console.print(f"  • {point}")
        
        console.print(f"\n[dim]File type: {result.file_type}[/dim]")
        console.print(f"[dim]Size: {result.metadata.get('size', 0)} bytes[/dim]")
        
        # Save if requested
        if output:
            analysis_text = f"Summary: {result.summary}\n\nKey Points:\n"
            analysis_text += "\n".join([f"- {p}" for p in result.key_points])
            output.write_text(analysis_text)
            console.print(f"\n[green]✅ Analysis saved to {output}[/green]")
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def create_spec(
    feature_description: str = typer.Argument(..., help="Feature description"),
    output: Path = typer.Option("feature_spec.md", "--output", "-o", help="Output file"),
    include_diagrams: bool = typer.Option(True, "--diagrams/--no-diagrams", help="Generate diagrams with Flux 2"),
    flux_api_key: Optional[str] = typer.Option(None, "--flux-key", help="Flux 2 API key"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Create comprehensive feature specification document.
    
    Includes architecture, requirements, user stories, and diagrams.
    
    Examples:
        clippy-swe create-spec "User authentication system"
        clippy-swe create-spec "Real-time chat feature" --diagrams --flux-key YOUR_KEY
    """
    setup_logging(verbose)
    
    try:
        from .document_processor import DocumentProcessor
        
        console.print(f"[cyan]Creating feature specification for: {feature_description}[/cyan]")
        
        agent_config = ClippySWEConfig(observer_mode=True)
        agent = ClippySWEAgent(config=agent_config)
        processor = DocumentProcessor(agent, flux_api_key=flux_api_key)
        
        result = processor.create_feature_spec(feature_description, output, include_diagrams)
        
        if result["success"]:
            console.print("\n[bold green]✅ Feature Spec Created![/bold green]")
            console.print(f"[cyan]Output: {result['output_path']}[/cyan]")
            console.print(f"[cyan]Sections: {result['sections']}[/cyan]")
            console.print(f"[cyan]Diagrams: {result['diagrams_generated']}[/cyan]")
            console.print(f"[cyan]Word count: {result['word_count']}[/cyan]")
        else:
            console.print(f"\n[bold red]❌ Creation Failed: {result.get('error')}[/bold red]")
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def analyze_recording(
    recording_path: Path = typer.Argument(..., help="Audio/video recording file"),
    transcript: Optional[Path] = typer.Option(None, "--transcript", "-t", help="Existing transcript file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save analysis to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Analyze audio/video recordings.
    
    Generates transcript, summary, action items, and insights.
    
    Examples:
        clippy-swe analyze-recording meeting.mp4
        clippy-swe analyze-recording call.mp3 --transcript transcript.txt
    """
    setup_logging(verbose)
    
    try:
        from .document_processor import DocumentProcessor
        
        if not recording_path.exists():
            console.print(f"[red]File not found: {recording_path}[/red]")
            sys.exit(1)
        
        console.print(f"[cyan]Analyzing recording: {recording_path}[/cyan]")
        
        agent_config = ClippySWEConfig()
        agent = ClippySWEAgent(config=agent_config)
        processor = DocumentProcessor(agent)
        
        result = processor.analyze_recording(recording_path, transcript)
        
        if result["success"]:
            console.print("\n[bold green]✅ Recording Analyzed![/bold green]")
            console.print(Panel(result["analysis"], title="📊 Analysis", border_style="green"))
            
            if output:
                output_text = f"Recording: {recording_path}\n\n"
                output_text += f"Transcript:\n{result['transcript']}\n\n"
                output_text += f"Analysis:\n{result['analysis']}"
                output.write_text(output_text)
                console.print(f"\n[green]✅ Analysis saved to {output}[/green]")
        else:
            console.print(f"\n[bold red]❌ Analysis Failed: {result.get('error')}[/bold red]")
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def generate_image(
    prompt: str = typer.Argument(..., help="Image generation prompt"),
    output: Path = typer.Option("generated_image.png", "--output", "-o", help="Output image file"),
    width: int = typer.Option(1024, "--width", "-w", help="Image width"),
    height: int = typer.Option(1024, "--height", "-h", help="Image height"),
    flux_api_key: Optional[str] = typer.Option(None, "--flux-key", help="Flux 2 API key"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Generate images using Flux 2 model.
    
    High-quality image generation from text prompts.
    
    Examples:
        clippy-swe generate-image "A futuristic city skyline" --flux-key YOUR_KEY
        clippy-swe generate-image "Software architecture diagram" --width 1920 --height 1080
    """
    setup_logging(verbose)
    
    try:
        from .document_processor import DocumentProcessor
        
        console.print(f"[cyan]Generating image: {prompt[:50]}...[/cyan]")
        
        agent_config = ClippySWEConfig()
        agent = ClippySWEAgent(config=agent_config)
        processor = DocumentProcessor(agent, flux_api_key=flux_api_key)
        
        result = processor.generate_image_flux2(prompt, output, width, height)
        
        if result["success"]:
            console.print("\n[bold green]✅ Image Generated![/bold green]")
            console.print(f"[cyan]Output: {result['output_path']}[/cyan]")
            console.print(f"[cyan]Dimensions: {result['dimensions']}[/cyan]")
        else:
            console.print(f"\n[bold red]❌ Generation Failed: {result.get('error')}[/bold red]")
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
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
