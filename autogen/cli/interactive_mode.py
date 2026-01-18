# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
Interactive Mode for Clippy SWE Agent

Provides an interactive conversational interface similar to GitHub Copilot CLI,
with support for file attachments, shell commands, and session management.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from ..import_utils import optional_import_block

with optional_import_block():
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.syntax import Syntax

logger = logging.getLogger(__name__)


class InteractiveSession:
    """
    Interactive session manager for Clippy SWE Agent.
    
    Provides GitHub Copilot CLI-style interactive mode with:
    - Natural language prompts
    - File attachments (@filename)
    - Shell command execution (!command)
    - Slash commands (/model, /clear, etc.)
    - Session persistence
    """

    def __init__(self, agent, session_file: Path | None = None):
        """
        Initialize interactive session.
        
        Args:
            agent: ClippySWEAgent instance
            session_file: Optional path to save/load session
        """
        self.agent = agent
        self.session_file = session_file or Path.cwd() / ".clippy_session.json"
        self.console = Console()
        self.conversation_history: list[dict[str, Any]] = []
        self.attached_files: list[Path] = []
        self.current_model = None
        self._load_session()

    def _load_session(self) -> None:
        """Load previous session if exists."""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    data = json.load(f)
                    self.conversation_history = data.get("history", [])
                    logger.info(f"Loaded session with {len(self.conversation_history)} messages")
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")

    def _save_session(self) -> None:
        """Save current session."""
        try:
            with open(self.session_file, "w") as f:
                json.dump(
                    {
                        "history": self.conversation_history,
                        "attached_files": [str(f) for f in self.attached_files],
                        "current_model": self.current_model,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def run(self) -> None:
        """Start interactive session."""
        self.console.print(
            Panel.fit(
                "[bold cyan]Clippy SWE Agent - Interactive Mode[/bold cyan]\n"
                "Type your request, use @ to attach files, ! for shell commands, / for commands\n"
                "Type 'exit' or 'quit' to end session",
                title="🤖 Interactive Session",
                border_style="cyan",
            )
        )

        while True:
            try:
                # Get user input
                prompt_text = self._build_prompt()
                user_input = Prompt.ask(prompt_text)

                if not user_input.strip():
                    continue

                # Check for exit
                if user_input.lower() in ["exit", "quit", "bye"]:
                    self.console.print("[yellow]Ending session...[/yellow]")
                    self._save_session()
                    break

                # Process input
                response = self._process_input(user_input)

                # Display response
                if response:
                    self._display_response(response)

                # Save session after each interaction
                self._save_session()

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Session interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logger.error(f"Interactive session error: {e}", exc_info=True)

    def _build_prompt(self) -> str:
        """Build prompt text with context indicators."""
        prompt = "You"
        if self.attached_files:
            prompt += f" ({len(self.attached_files)} files)"
        if self.current_model:
            prompt += f" [{self.current_model}]"
        return f"[bold green]{prompt}>[/bold green]"

    def _process_input(self, user_input: str) -> dict[str, Any] | None:
        """
        Process user input and return response.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response dictionary or None
        """
        # Handle slash commands
        if user_input.startswith("/"):
            return self._handle_slash_command(user_input)

        # Handle shell commands
        if user_input.startswith("!"):
            return self._handle_shell_command(user_input[1:])

        # Handle file attachments
        if "@" in user_input:
            self._handle_file_attachment(user_input)
            # Remove @ mentions from the actual query
            user_input = self._strip_file_mentions(user_input)

        # Build context from attached files
        context = self._build_context()

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})

        # Execute task with agent
        result = self.agent.execute_task(
            task_description=user_input, task_type="general", context=context
        )

        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": result.get("result", "")})

        return result

    def _handle_slash_command(self, command: str) -> dict[str, Any]:
        """Handle slash commands like /model, /clear, etc."""
        parts = command[1:].split()
        cmd = parts[0].lower() if parts else ""

        if cmd == "clear":
            self.conversation_history = []
            self.attached_files = []
            self.console.print("[green]Session cleared![/green]")
            return {"status": "cleared"}

        elif cmd == "model":
            if len(parts) > 1:
                self.current_model = parts[1]
                self.console.print(f"[green]Switched to model: {self.current_model}[/green]")
            else:
                self.console.print(f"[cyan]Current model: {self.current_model or 'default'}[/cyan]")
            return {"status": "model_info", "model": self.current_model}

        elif cmd == "usage":
            task_count = len(self.agent.task_history.tasks)
            msg_count = len(self.conversation_history)
            self.console.print(f"[cyan]Tasks completed: {task_count}[/cyan]")
            self.console.print(f"[cyan]Messages in session: {msg_count}[/cyan]")
            return {"status": "usage", "tasks": task_count, "messages": msg_count}

        elif cmd == "cwd":
            cwd = Path.cwd()
            self.console.print(f"[cyan]Current directory: {cwd}[/cyan]")
            return {"status": "cwd", "path": str(cwd)}

        elif cmd == "resume" or cmd == "continue":
            if self.conversation_history:
                self.console.print(f"[green]Resumed session with {len(self.conversation_history)} messages[/green]")
            else:
                self.console.print("[yellow]No previous session to resume[/yellow]")
            return {"status": "resumed", "message_count": len(self.conversation_history)}

        elif cmd == "files":
            if self.attached_files:
                self.console.print("[cyan]Attached files:[/cyan]")
                for f in self.attached_files:
                    self.console.print(f"  - {f}")
            else:
                self.console.print("[yellow]No files attached[/yellow]")
            return {"status": "files", "files": [str(f) for f in self.attached_files]}

        elif cmd == "detach":
            self.attached_files = []
            self.console.print("[green]All files detached[/green]")
            return {"status": "detached"}

        elif cmd == "help":
            self._show_help()
            return {"status": "help"}

        else:
            self.console.print(f"[red]Unknown command: /{cmd}[/red]")
            self.console.print("[yellow]Type /help for available commands[/yellow]")
            return {"status": "error", "message": f"Unknown command: {cmd}"}

    def _handle_shell_command(self, command: str) -> dict[str, Any]:
        """Execute shell command and return output."""
        self.console.print(f"[dim]Executing: {command}[/dim]")

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )

            output = result.stdout if result.returncode == 0 else result.stderr

            if output:
                syntax = Syntax(output, "bash", theme="monokai", line_numbers=False)
                self.console.print(syntax)

            return {
                "status": "executed",
                "command": command,
                "exit_code": result.returncode,
                "output": output,
            }

        except subprocess.TimeoutExpired:
            self.console.print("[red]Command timed out[/red]")
            return {"status": "timeout", "command": command}
        except Exception as e:
            self.console.print(f"[red]Command failed: {e}[/red]")
            return {"status": "error", "command": command, "error": str(e)}

    def _handle_file_attachment(self, user_input: str) -> None:
        """Extract and attach files mentioned with @."""
        import re

        # Find @mentions
        mentions = re.findall(r"@([^\s]+)", user_input)

        for mention in mentions:
            file_path = Path(mention)
            if file_path.exists() and file_path.is_file():
                if file_path not in self.attached_files:
                    self.attached_files.append(file_path)
                    self.console.print(f"[green]Attached: {file_path}[/green]")
            else:
                self.console.print(f"[yellow]File not found: {mention}[/yellow]")

    def _strip_file_mentions(self, text: str) -> str:
        """Remove @file mentions from text."""
        import re

        return re.sub(r"@[^\s]+", "", text).strip()

    def _build_context(self) -> dict[str, Any]:
        """Build context from attached files and environment."""
        context = {
            "attached_files": [],
            "cwd": str(Path.cwd()),
            "session_messages": len(self.conversation_history),
        }

        # Read attached file contents
        for file_path in self.attached_files:
            try:
                with open(file_path) as f:
                    content = f.read()
                    context["attached_files"].append(
                        {"path": str(file_path), "content": content[:5000]}  # Limit content size
                    )
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")

        return context

    def _display_response(self, response: dict[str, Any]) -> None:
        """Display agent response."""
        if response.get("status") == "completed":
            result_text = response.get("result", "No result")

            # Check if result looks like code
            if "```" in result_text or "\n" in result_text and len(result_text) > 100:
                self.console.print(Panel(Markdown(result_text), title="✨ Response", border_style="green"))
            else:
                self.console.print(f"[bold green]Clippy:[/bold green] {result_text}")

        elif response.get("status") == "failed":
            self.console.print(f"[red]Error: {response.get('error', 'Unknown error')}[/red]")
        else:
            # For command responses, just print status
            if response.get("status") not in ["cleared", "model_info", "executed"]:
                self.console.print(f"[dim]{response}[/dim]")

    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold cyan]Clippy SWE Interactive Mode - Commands[/bold cyan]

[bold]Natural Language:[/bold]
  Just type your request naturally

[bold]File Attachments:[/bold]
  @filename     Attach a file for context
  /files        List attached files
  /detach       Remove all attached files

[bold]Shell Commands:[/bold]
  !command      Execute a shell command

[bold]Slash Commands:[/bold]
  /clear        Clear conversation history
  /model [name] Switch or view current model
  /usage        Show usage statistics
  /cwd          Show current working directory
  /resume       Resume previous session
  /help         Show this help message

[bold]Session Commands:[/bold]
  exit, quit    End interactive session

[bold]Examples:[/bold]
  Create a Flask API
  @auth.py Fix the authentication bug in this file
  !git status
  /model gpt-4
        """
        self.console.print(Panel(help_text, title="Help", border_style="cyan"))
