# Clippy SWE Agent - Quick Start Guide

## What is Clippy SWE Agent?

Clippy SWE (Software Engineering) Agent is an autonomous AI agent powered by the Clippy Kernel framework. It provides a CLI interface similar to GitHub Copilot CLI, but with enhanced capabilities:

- 🤖 **Fully Autonomous**: Completes complex tasks independently
- 🪟 **Windows Integration**: Native desktop automation (Windows)
- 👁️ **Observer Mode**: Watch the agent work in real-time
- 🎯 **Multi-Agent**: Specialized agents collaborate on tasks
- 📊 **Task History**: Complete audit trail of all work

## Prerequisites

- Python 3.10 - 3.13
- OpenAI API key (or compatible LLM API)
- Windows OS (for Windows automation features)

## Installation

### Option 1: Quick Install (Recommended)

```bash
# Clone and navigate to repository
cd Clippy-Kernel

# Run quick start script
bash scripts/quickstart_clippy_swe.sh
```

### Option 2: Manual Install

```bash
# Basic installation
pip install -e ".[openai,mcp-proxy-gen]"

# Full installation (all features)
pip install -e ".[openai,windows-clippy-mcp,mcp-proxy-gen,browser-use]"
```

## Configuration

### 1. Create API Configuration

Create `OAI_CONFIG_LIST` file:

```json
[
  {
    "model": "gpt-4",
    "api_key": "sk-your-openai-api-key"
  }
]
```

### 2. Initialize Agent

```bash
clippy-swe init
```

This creates `.clippy_swe_config.json` with default settings.

## Basic Usage

### Execute a Coding Task

```bash
clippy-swe task "Create a Flask REST API with JWT authentication"
```

### With Observer Mode (See Agent Work)

```bash
clippy-swe task "Fix the bug in auth.py" --observer --type coding
```

### Research Task

```bash
clippy-swe task "Research best practices for Python async/await" --type research
```

### System Task

```bash
clippy-swe task "Analyze system performance and suggest optimizations" --type system
```

### Windows Automation (Windows Only)

```bash
clippy-swe windows "Take a screenshot and save to Desktop"
```

## CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `task` | Execute autonomous task | `clippy-swe task "Description"` |
| `windows` | Windows automation | `clippy-swe windows "Task"` |
| `status` | Show agent status | `clippy-swe status` |
| `history` | View task history | `clippy-swe history` |
| `init` | Initialize config | `clippy-swe init` |
| `version` | Show version | `clippy-swe version` |

## Task Types

- `general` - General-purpose tasks (default)
- `coding` - Software development tasks
- `system` - System administration
- `research` - Research and analysis
- `debug` - Debugging tasks
- `deploy` - Deployment tasks
- `test` - Testing tasks
- `review` - Code review tasks

## Python API

```python
from autogen.cli import ClippySWEAgent, ClippySWEConfig

# Configure
config = ClippySWEConfig(
    observer_mode=True,
    autonomous_mode=True,
)

# Create agent
agent = ClippySWEAgent(config=config)

# Execute task
result = agent.execute_task(
    "Create a REST API",
    task_type="coding"
)

print(f"Status: {result['status']}")
```

## Examples

See `examples/clippy_swe_agent_example.py` for comprehensive examples.

## Troubleshooting

### "No module named 'pydantic'"

Install dependencies:
```bash
pip install -e ".[openai,mcp-proxy-gen]"
```

### "LLM configuration not found"

Create `OAI_CONFIG_LIST` with your API key.

### Windows features not working

Windows automation only works on Windows OS.

## Next Steps

1. ✅ Install Clippy SWE Agent
2. ✅ Configure API keys
3. ✅ Try basic task
4. 📖 Read full guide: [CLIPPY_SWE_AGENT_GUIDE.md](CLIPPY_SWE_AGENT_GUIDE.md)
5. 🔨 Explore examples: `examples/clippy_swe_agent_example.py`
6. 🤝 Contribute: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Documentation

- **Full Guide**: [CLIPPY_SWE_AGENT_GUIDE.md](CLIPPY_SWE_AGENT_GUIDE.md)
- **Main README**: [README.md](README.md)
- **API Docs**: See docstrings in source code

## Support

- GitHub Issues: https://github.com/dayour/Clippy-Kernel/issues
- Discussions: https://github.com/dayour/Clippy-Kernel/discussions

## License

Apache License 2.0 - See [LICENSE](LICENSE)
