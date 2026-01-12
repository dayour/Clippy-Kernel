# Clippy SWE Agent - Autonomous Software Engineering Agent

## Overview

Clippy SWE is an autonomous software engineering agent that provides a powerful CLI interface similar to GitHub Copilot CLI, but with enhanced capabilities for autonomous coding, Windows automation, and multi-agent orchestration.

## Features

- 🤖 **Autonomous Operation**: Fully autonomous agent that can complete complex tasks independently
- 🔧 **Multi-Agent Collaboration**: Specialized agents work together (Software Engineer, System Admin, Researcher, Coordinator)
- 🪟 **Windows Integration**: Native Windows desktop automation and application interaction
- 🎯 **Task Orchestration**: Intelligent task delegation and coordination
- 👁️ **Observer Mode**: Visual feedback showing agent actions in real-time
- 📊 **Task History**: Complete history of all executed tasks
- ⚡ **Background Execution**: Run tasks in background without blocking
- 🛠️ **Tool Integration**: Extensive toolkit for development, web scraping, and system operations

## Installation

### Basic Installation

```bash
pip install -e ".[openai,mcp-proxy-gen]"
```

### Full Installation with All Features

```bash
# Using UV (faster)
uv pip install -e ".[openai,windows-clippy-mcp,mcp-proxy-gen,browser-use]"

# Using pip
pip install -e ".[openai,windows-clippy-mcp,mcp-proxy-gen,browser-use]"
```

## Configuration

### 1. Set up API Keys

Create an `OAI_CONFIG_LIST` file with your API keys:

```json
[
  {
    "model": "gpt-4",
    "api_key": "your-openai-api-key-here"
  }
]
```

### 2. Initialize Configuration

```bash
clippy-swe init --workspace ./my-workspace
```

This creates a `.clippy_swe_config.json` file with default settings.

### 3. Customize Configuration (Optional)

Edit `.clippy_swe_config.json`:

```json
{
  "llm_config_path": "OAI_CONFIG_LIST",
  "autonomous_mode": true,
  "observer_mode": false,
  "background_mode": false,
  "max_iterations": 50,
  "enable_windows_automation": true,
  "enable_app_interaction": true,
  "enable_web_tools": true,
  "enable_code_execution": true,
  "require_confirmation": false,
  "safe_mode": false
}
```

## Usage

### Basic Commands

#### Execute a Task

```bash
# General task
clippy-swe task "Create a Flask REST API with JWT authentication"

# Coding task with project context
clippy-swe task "Fix the bug in auth.py" --type coding --project ./myapp

# Research task
clippy-swe task "Research best practices for React hooks" --type research

# System administration task
clippy-swe task "Analyze system performance and provide optimization recommendations" --type system
```

#### Windows Automation

```bash
# Execute Windows-specific task
clippy-swe windows "Take a screenshot and save to Desktop"

# Interact with specific application
clippy-swe windows "Open Visual Studio Code and create a new Python project" --app "Code"

# System monitoring
clippy-swe windows "Monitor CPU usage and alert if >80%"
```

#### Check Status

```bash
# Display system and agent status
clippy-swe status

# Verbose status with details
clippy-swe status --verbose
```

#### View History

```bash
# List recent tasks
clippy-swe history

# Show more tasks
clippy-swe history --limit 20

# View specific task details
clippy-swe history --id 5 --verbose
```

### Advanced Usage

#### Observer Mode

Enable visual feedback to see what the agent is doing:

```bash
clippy-swe task "Build a web scraper" --observer
```

#### Background Mode

Run tasks in background without UI:

```bash
clippy-swe task "Run all tests and generate report" --background
```

#### Custom Configuration

Use a specific configuration file:

```bash
clippy-swe task "Deploy to production" --config ./prod-config.json
```

#### Maximum Iterations

Control agent iteration limit:

```bash
clippy-swe task "Complex refactoring task" --max-iterations 100
```

### Task Types

- `general`: General-purpose tasks (default)
- `coding`: Software development and coding tasks
- `system`: System administration and operations
- `research`: Research and analysis tasks
- `debug`: Debugging and troubleshooting
- `deploy`: Deployment and DevOps tasks
- `test`: Testing and quality assurance
- `review`: Code review and analysis

## Examples

### Example 1: Create a Web Application

```bash
clippy-swe task "Create a FastAPI application with user authentication, database integration using SQLAlchemy, and REST endpoints for CRUD operations" --type coding --observer
```

### Example 2: Research and Compare

```bash
clippy-swe task "Research and compare Python async frameworks (asyncio, Trio, Curio) with pros, cons, and use case recommendations" --type research
```

### Example 3: System Analysis

```bash
clippy-swe task "Analyze current system resource usage, identify bottlenecks, and provide optimization recommendations" --type system --observer
```

### Example 4: Code Review

```bash
clippy-swe task "Review the code in ./src/api and provide security, performance, and maintainability feedback" --type review --project ./myproject
```

### Example 5: Windows Automation

```bash
# Windows-specific tasks (Windows only)
clippy-swe windows "Check Windows Update status and list pending updates"

clippy-swe windows "Open PowerShell and run system diagnostics" --app "PowerShell"
```

### Example 6: Background Task

```bash
# Run long-running task in background
clippy-swe task "Run full test suite, generate coverage report, and email results" --background
```

## Python API

You can also use Clippy SWE Agent programmatically:

```python
from autogen.cli import ClippySWEAgent, ClippySWEConfig

# Configure the agent
config = ClippySWEConfig(
    observer_mode=True,
    autonomous_mode=True,
    max_iterations=30,
)

# Create the agent
agent = ClippySWEAgent(config=config)

# Execute a task
result = agent.execute_task(
    "Create a REST API with authentication",
    task_type="coding"
)

print(f"Status: {result['status']}")
print(f"Result: {result['result']}")
```

### Task Execution with Context

```python
result = agent.execute_task(
    task_description="Implement caching layer",
    task_type="coding",
    context={
        "framework": "Flask",
        "cache_backend": "Redis",
        "requirements": "High performance, TTL support"
    }
)
```

### Windows Automation API

```python
result = agent.execute_windows_task(
    "Monitor system resources and generate report",
    app_name="Task Manager"
)
```

### Check System Status

```python
status = agent.get_system_status()
print(f"Agent Initialized: {status['agent']['initialized']}")
print(f"LLM Configured: {status['agent']['llm_configured']}")
print(f"CPU Usage: {status['resources']['cpu_percent']}%")
```

### View Task History

```python
# Get recent tasks
recent_tasks = agent.list_recent_tasks(limit=10)

for task in recent_tasks:
    print(f"Task #{task['id']}: {task['description']}")
    print(f"Status: {task['status']}")
    print(f"Type: {task['type']}")
    print()

# Get specific task
task = agent.get_task_by_id(5)
if task:
    print(f"Result: {task['result']}")
```

## Architecture

### Agent Roles

The Clippy SWE Agent uses a multi-agent architecture with specialized roles:

1. **Software Engineer**: Expert in coding, architecture, and development
2. **System Administrator**: Handles system operations, automation, and infrastructure
3. **Researcher**: Investigates problems, researches solutions, and provides analysis
4. **Task Coordinator**: Orchestrates team collaboration and ensures task completion

### Agent Selection

The system automatically selects appropriate agents based on task type:

- **Coding tasks**: Engineer + Researcher + Coordinator
- **System tasks**: SysAdmin + Engineer + Coordinator
- **Research tasks**: Researcher + Engineer + Coordinator
- **Debug tasks**: Engineer + Researcher + Coordinator

## Integration with Clippy Kernel

Clippy SWE Agent integrates seamlessly with Clippy Kernel features:

- **Agent Dev Team**: Use agent development teams for complex projects
- **MCP Integration**: Access Model Control Protocol tools and services
- **Windows-Clippy-MCP**: Full Windows desktop automation capabilities
- **ClippyKernelToolkit**: Extensive toolkit for development workflows

## Safety and Security

### Safe Mode

Enable safe mode for additional safety checks:

```bash
clippy-swe task "Delete old log files" --config safe-config.json
```

In `safe-config.json`:
```json
{
  "safe_mode": true,
  "require_confirmation": true
}
```

### Confirmation Mode

Require confirmation for critical operations:

```python
config = ClippySWEConfig(require_confirmation=True)
```

## Troubleshooting

### LLM Configuration Not Found

```
Error: OAI_CONFIG_LIST not found
```

**Solution**: Create `OAI_CONFIG_LIST` file with your API keys.

### Import Errors

```
Error: The clippy-swe command requires additional dependencies
```

**Solution**: Install with mcp-proxy-gen extras:
```bash
pip install -e ".[mcp-proxy-gen]"
```

### Windows Automation Not Available

```
Error: Windows automation only available on Windows
```

**Solution**: Windows-specific features only work on Windows OS.

## Performance Tips

1. **Use Observer Mode Sparingly**: Observer mode adds overhead; disable for production
2. **Adjust Max Iterations**: Set appropriate limits based on task complexity
3. **Background Mode**: Use for long-running tasks to free up terminal
4. **Task History**: Regularly review history to optimize task descriptions

## Contributing

Contributions are welcome! Areas for improvement:

- Additional specialized agents
- Enhanced Windows automation
- More tool integrations
- Performance optimizations
- Documentation and examples

## License

Clippy SWE Agent is part of Clippy Kernel and licensed under the Apache License, Version 2.0.

## Support

- GitHub Issues: https://github.com/dayour/Clippy-Kernel/issues
- Discussions: https://github.com/dayour/Clippy-Kernel/discussions
- Documentation: See `CLIPPY_KERNEL_DEVELOPER_GUIDE.md`

## Related Documentation

- [Clippy Kernel README](../README.md)
- [Agent Development Team](../examples/agent_dev_team/)
- [Clippy MCP Integration](../examples/clippy_mcp/)
- [Windows-Clippy-MCP Guide](../README_WINDOWS_CLIPPY_MCP.md)
