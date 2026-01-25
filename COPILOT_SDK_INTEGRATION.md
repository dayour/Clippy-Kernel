# GitHub Copilot SDK Integration Guide

## Overview

Clippy SWE Agent now integrates the GitHub Copilot SDK to provide enhanced AI capabilities with support for multiple model providers including OpenAI (Codex/GPT), Anthropic (Claude), and Google (Gemini).

## Features

### Multi-Model Support

Switch between different AI models based on your needs:

- **OpenAI GPT-4/GPT-5** (Codex)
  - Fast code generation and prototyping
  - Strong GitHub integration
  - Best for: Quick MVPs, automation, rapid prototyping
  - Context window: Up to 128K tokens

- **Anthropic Claude 3/4**
  - Deep code understanding and reasoning
  - Excellent multi-file refactoring
  - Best for: Complex codebases, production code, enterprise
  - Context window: Up to 200K tokens
  - Highest benchmark scores (SWE-bench: 80.9%)

- **Google Gemini Pro/Ultra**
  - Massive context window (up to 1M tokens)
  - Strong multi-modal capabilities
  - Best for: Large codebases, data-heavy tasks, algorithmic coding
  - Excellent for real-time data integration

### GitHub Copilot SDK Features

1. **Multi-Turn Conversations**
   - Session history with context awareness
   - Continuity across multiple interactions

2. **Programmable Tools**
   - Register custom tools that AI can invoke
   - Expose application capabilities as tools

3. **Streaming Responses**
   - Real-time output streaming
   - Low-latency interactions

4. **Session Management**
   - Create, manage, and persist sessions
   - Resume conversations

5. **Authentication**
   - GitHub token authentication
   - Bring-your-own-key support

## Installation

```bash
# Install with Copilot SDK support
pip install -e ".[copilot-sdk,mcp-proxy-gen]"

# Install specific providers
pip install -e ".[openai]"              # OpenAI/Codex
pip install -e ".[anthropic]"           # Claude
pip install -e ".[gemini]"              # Gemini
```

## Configuration

### API Keys

Set up API keys in your configuration file or environment:

**Option 1: Configuration File**

Create `.clippy_swe_config.json`:

```json
{
  "use_copilot_sdk": true,
  "copilot_model": "gpt-4",
  "copilot_provider": "openai",
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-...",
  "google_api_key": "AIza...",
  "github_token": "ghp_...",
  "enable_streaming": true,
  "context_window_size": 128000
}
```

**Option 2: Environment Variables**

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export GITHUB_TOKEN=ghp_...
```

**Option 3: OAI_CONFIG_LIST (Legacy)**

```json
[
  {
    "model": "gpt-4",
    "api_key": "sk-..."
  }
]
```

## Usage

### Switching Models

```bash
# List available models
clippy-swe models --list

# Set default model to GPT-4
clippy-swe models --set gpt-4 --provider openai

# Set to Claude for deep code understanding
clippy-swe models --set claude-3-opus --provider anthropic

# Set to Gemini for large context
clippy-swe models --set gemini-pro --provider google

# Show current configuration
clippy-swe models --current
```

### Using Different Models

#### OpenAI/Codex (Fast, Versatile)

```bash
# Set OpenAI as default
clippy-swe models --set gpt-4 --provider openai

# Execute task with GPT-4
clippy-swe task "Create a REST API" --type coding

# Interactive mode with GPT-5
clippy-swe interactive
> /model gpt-5
> Create a Flask application
```

**Best for:**
- Rapid prototyping
- Quick automation
- Simple to medium complexity tasks
- Fast iterations

#### Claude (Deep Reasoning, Complex Refactoring)

```bash
# Set Claude as default
clippy-swe models --set claude-3-opus --provider anthropic

# Execute complex refactoring
clippy-swe task "Refactor authentication system across 10 files" --type coding --observer

# Resolve complex GitHub issue
clippy-swe resolve-issue owner/repo 456 --create-pr
```

**Best for:**
- Multi-file refactoring
- Complex architectural changes
- Production-grade code
- Enterprise applications
- Security-critical code

#### Gemini (Massive Context, Multi-Modal)

```bash
# Set Gemini as default
clippy-swe models --set gemini-1.5-pro --provider google

# Analyze large codebase
clippy-swe task "Analyze entire codebase and suggest optimizations" --type research

# Process large documents
clippy-swe analyze-doc huge_specification.pdf
```

**Best for:**
- Large codebases (1M+ tokens)
- Data-heavy tasks
- Algorithmic coding
- Multi-modal workflows
- Real-time data integration

### SDK Features in Action

#### Multi-Turn Conversations

```bash
clippy-swe interactive

You> Create a user authentication system
Clippy: [Generates auth system...]

You> Add password reset functionality
Clippy: [Extends with password reset, remembers previous context...]

You> Now add 2FA support
Clippy: [Adds 2FA, maintains full context of auth system...]
```

#### Tool Execution

Tools are automatically registered and can be invoked by the AI:

```python
from autogen.cli import ClippySWEAgent, ClippySWEConfig

config = ClippySWEConfig(use_copilot_sdk=True)
agent = ClippySWEAgent(config=config)

# Tools from ClippyKernelToolkit are automatically available
# AI can invoke: analyze_codebase, run_code_quality_check, etc.
```

#### Streaming Responses

```bash
# Enable streaming in config
echo '{"enable_streaming": true}' > .clippy_swe_config.json

# Real-time output as AI generates
clippy-swe task "Write a complex algorithm" --observer
```

## Model Comparison

### Feature Matrix

| Feature | GPT-4/5 (Codex) | Claude 3/4 | Gemini Pro/Ultra |
|---------|-----------------|------------|------------------|
| **Speed** | Fast ⚡⚡⚡ | Medium ⚡⚡ | Fast ⚡⚡⚡ |
| **Context** | 128K tokens | 200K tokens | 1M tokens 🏆 |
| **Code Quality** | Good ⭐⭐⭐ | Excellent ⭐⭐⭐⭐ | Good ⭐⭐⭐ |
| **Multi-File** | Basic | Excellent 🏆 | Good |
| **Reasoning** | Good | Excellent 🏆 | Very Good |
| **Cost** | $$ | $$$ | $ |
| **SWE-bench** | 80% | 80.9% 🏆 | N/A |
| **Best For** | Prototyping | Enterprise | Large Context |

### When to Use Each Model

**Use GPT-4/GPT-5 (OpenAI/Codex) when:**
- Need fast results
- Prototyping or MVPs
- Simple to medium tasks
- Tight GitHub integration needed
- Cost is a concern

**Use Claude 3/4 (Anthropic) when:**
- Complex multi-file refactoring
- Production-grade code needed
- Deep reasoning required
- Enterprise/regulated environment
- Code quality is critical

**Use Gemini Pro/Ultra (Google) when:**
- Analyzing large codebases
- Need huge context window
- Multi-modal tasks
- Algorithmic/competitive coding
- Real-time data integration

## Advanced Usage

### Python API with SDK

```python
from autogen.cli import ClippySWEAgent, ClippySWEConfig
from autogen.cli.copilot_sdk_client import CopilotSDKClient, ModelProvider

# Initialize with Copilot SDK
config = ClippySWEConfig(
    use_copilot_sdk=True,
    copilot_model="claude-3-opus",
    copilot_provider="anthropic",
    anthropic_api_key="sk-ant-...",
    enable_streaming=True,
    context_window_size=200000,
)

agent = ClippySWEAgent(config=config)

# Execute task with Claude
result = agent.execute_task(
    "Refactor the entire authentication system",
    task_type="coding"
)

# Access SDK client directly
sdk_client = agent.copilot_sdk_client
session = sdk_client.create_session(
    model="gemini-1.5-pro",
    provider=ModelProvider.GOOGLE,
    context_window=1000000,
)

# Send message with streaming
async for chunk in await sdk_client.send_message(
    session.session_id,
    "Analyze this massive codebase",
    stream=True
):
    print(chunk["content"], end="")
```

### Registering Custom Tools

```python
from autogen.cli.copilot_sdk_client import CopilotSDKClient

client = CopilotSDKClient(openai_api_key="...")

# Register custom tool
def deploy_to_production(environment: str) -> str:
    # Your deployment logic
    return f"Deployed to {environment}"

client.register_tool(
    name="deploy",
    func=deploy_to_production,
    description="Deploy application to production",
    parameters={
        "type": "object",
        "properties": {
            "environment": {
                "type": "string",
                "enum": ["staging", "production"],
                "description": "Target environment"
            }
        },
        "required": ["environment"]
    }
)

# AI can now call this tool
```

### Switching Models Dynamically

```bash
# Interactive mode with model switching
clippy-swe interactive

You> /model gpt-4
Switched to model: gpt-4

You> Create a quick prototype
Clippy: [Fast response with GPT-4...]

You> /model claude-3-opus
Switched to model: claude-3-opus

You> Now refactor it for production
Clippy: [Deep refactoring with Claude...]

You> /model gemini-pro
Switched to model: gemini-pro

You> Analyze the entire codebase for patterns
Clippy: [Comprehensive analysis with large context...]
```

## Benefits Over Standard Implementation

1. **Multi-Provider Support**
   - Not locked to single provider
   - Use best model for each task
   - Fallback options if one provider is down

2. **Enhanced Context Management**
   - Up to 1M tokens with Gemini
   - Better handling of large codebases
   - More effective multi-file operations

3. **Tool Execution**
   - AI can call registered tools
   - Agentic workflows
   - Extended capabilities

4. **Streaming**
   - Real-time feedback
   - Better user experience
   - Lower latency perception

5. **Session Persistence**
   - Resume conversations
   - Maintain context across restarts
   - Better continuity

## Troubleshooting

### API Key Errors

```
Error: API key not configured
```

**Solution:** Add API keys to config or environment variables.

### Model Not Available

```
Error: Model not found
```

**Solution:** Check available models with `clippy-swe models --list`

### Context Window Exceeded

```
Error: Token limit exceeded
```

**Solution:** Use a model with larger context (Gemini) or clear session history.

## Migration Guide

### From Standard Clippy SWE

```bash
# Before (standard)
clippy-swe task "Create API"

# After (with SDK, same command)
clippy-swe task "Create API"

# Configure SDK
clippy-swe models --set claude-3-opus --provider anthropic
```

### From GitHub Copilot CLI

```bash
# GitHub Copilot CLI
copilot "Create a function"

# Clippy SWE with SDK
clippy-swe interactive
> Create a function
```

### From SWE-agent

```bash
# SWE-agent
python run.py --model gpt-4 --repo owner/repo --issue 123

# Clippy SWE with SDK
clippy-swe models --set gpt-4 --provider openai
clippy-swe resolve-issue owner/repo 123
```

## Best Practices

1. **Choose the Right Model**
   - Use GPT-4 for fast iterations
   - Use Claude for complex refactoring
   - Use Gemini for large context analysis

2. **Enable Streaming**
   - Better user experience
   - Real-time feedback

3. **Session Management**
   - Use sessions for related tasks
   - Clear sessions periodically to manage costs

4. **Tool Registration**
   - Register application-specific tools
   - Let AI use your APIs

5. **Context Window**
   - Monitor token usage
   - Use larger models for bigger contexts

## References

- [GitHub Copilot SDK](https://github.com/github/copilot-sdk)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Google Gemini API](https://ai.google.dev/docs)

## Support

For issues or questions:
- GitHub Issues: https://github.com/dayour/Clippy-Kernel/issues
- Documentation: CLIPPY_SWE_AGENT_GUIDE.md
- Examples: examples/clippy_swe_agent_example.py
