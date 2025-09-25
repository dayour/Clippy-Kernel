# AG2 Multi-Agent AI Framework

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

AG2 (formerly AutoGen) is an open-source Python framework for building AI agents and facilitating cooperation among multiple agents. It requires **Python version >= 3.10, <= 3.13** and supports complex multi-agent conversation patterns, tool usage, real-time interactions, web browsing, model control protocol (MCP) integration, and various LLM integrations.

## Working Effectively

### Environment Setup
- **CRITICAL**: Set up proper Python environment first:
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

### Core Installation and Setup
- **RECOMMENDED**: Use `uv` package manager for faster installations:
  ```bash
  # Install uv if not available
  pip install uv
  # Install the framework with development dependencies
  uv pip install -e ".[dev]"
  ```
  **TIMEOUT WARNING**: Installation takes 8-15 minutes with uv, 15-25 minutes with pip. NEVER CANCEL. Set timeout to 45+ minutes.

- Traditional pip installation (slower but more compatible):
  ```bash
  pip install -e ".[dev]"
  ```
  
- If network timeouts occur (common in constrained environments):
  ```bash
  # Try basic installation first
  pip install -e . --timeout=600
  # Then add dev tools separately
  pip install pytest ruff pre-commit mypy --timeout=300
  ```

- **Alternative with uv** for constrained environments:
  ```bash
  uv pip install --timeout=600 -e . 
  uv pip install --timeout=300 pytest ruff pre-commit mypy
  ```

### Pre-commit Setup
- **ALWAYS** install pre-commit hooks after initial setup:
  ```bash
  pre-commit install
  ```

### Build and Test Commands
- **Core tests without LLMs** (most reliable for development):
  ```bash
  bash scripts/test-core-skip-llm.sh
  ```
  **TIMEOUT WARNING**: Takes 8-15 minutes. NEVER CANCEL. Set timeout to 30+ minutes.

- **Full test suite** (excluding LLM-dependent tests):
  ```bash
  bash scripts/test-skip-llm.sh
  ```
  **TIMEOUT WARNING**: Takes 20-35 minutes. NEVER CANCEL. Set timeout to 60+ minutes.

- **Linting and formatting**:
  ```bash
  bash scripts/lint.sh
  # Or individual commands:
  ruff check    # Linting
  ruff format   # Code formatting
  ```

### Documentation Build
- **Prerequisites**: Install Quarto 1.5.23+ (https://quarto.org/docs/download/)
- **Build MkDocs documentation**:
  ```bash
  pip install -e ".[docs]"
  ./scripts/docs_build_mkdocs.sh
  ```
  **TIMEOUT WARNING**: Takes 10-20 minutes. NEVER CANCEL. Set timeout to 45+ minutes.
  
- **Force rebuild** (cleans all temporary files):
  ```bash
  ./scripts/docs_build_mkdocs.sh --force
  ```

- **Serve documentation locally**:
  ```bash
  ./scripts/docs_serve_mkdocs.sh
  # Access at http://localhost:8000
  ```

### Key Optional Dependencies
AG2 supports numerous optional feature sets. Key ones for development:

- **Core LLM integrations**: `ag2[openai]`, `ag2[anthropic]`, `ag2[gemini]`
- **Real-time features**: `ag2[openai-realtime]`, `ag2[gemini-realtime]`, `ag2[twilio]`
- **Web capabilities**: `ag2[browser-use]`, `ag2[crawl4ai]`
- **Model Control Protocol**: `ag2[mcp]`, `ag2[mcp-proxy-gen]` 
- **Retrieval/RAG**: `ag2[retrievechat]`, `ag2[retrievechat-qdrant]`
- **Code execution**: `ag2[jupyter-executor]`
- **Data analysis**: `ag2[flaml]`

Install specific feature sets as needed:
```bash
# Example: Install with OpenAI and web browsing support
pip install -e ".[openai,browser-use]"
# or with uv:
uv pip install -e ".[openai,browser-use]"
```

## Validation Requirements

### Manual Testing Scenarios
After making changes, **ALWAYS** validate with these specific scenarios:

1. **Basic Agent Creation and Communication**:
   ```python
   from autogen import ConversableAgent, LLMConfig
   # Test agent creation, message handling, and basic conversation flows
   ```

2. **Multi-Agent Group Chat**:
   ```python
   from autogen.agentchat import run_group_chat
   from autogen.agentchat.group.patterns import AutoPattern
   # Test orchestration patterns and agent coordination
   ```

3. **Function/Tool Integration**:
   ```python
   from autogen import register_function
   # Test function registration, calling, and execution
   ```

4. **Code Execution Environments**:
   ```python
   from autogen.coding import LocalCommandLineCodeExecutor
   # Test code execution with different language support
   ```

5. **Configuration and LLM Client Integration**:
   ```python
   from autogen.llm_config import LLMConfig
   # Test configuration loading from JSON/environment
   ```

6. **Real-time Agent Interactions** (if using realtime features):
   ```python
   from autogen.agentchat.realtime_agent import RealtimeAgent
   # Test real-time voice/audio agent capabilities
   ```

7. **Model Control Protocol (MCP) Integration** (if using MCP):
   ```python
   # Test MCP server/client functionality for external tool integration
   ```

8. **Web Browsing and Crawling** (if using browser-use/crawl4ai):
   ```python
   # Test web browsing agent capabilities and web content extraction
   ```

### Required Validation Steps
- **ALWAYS** run linting before committing:
  ```bash
  pre-commit run --all-files
  ```
  Takes 3-8 minutes. NEVER CANCEL. Set timeout to 20+ minutes.

- **ALWAYS** run core tests for changes in autogen/:
  ```bash
  bash scripts/test-core-skip-llm.sh
  ```

- **Type checking** (for typed modules):
  ```bash
  mypy autogen/  # Limited to specific modules in pyproject.toml
  ```

## Common Issues and Network Limitations

### Installation Failures and Network Issues
- **Network timeouts** are common - use longer pip timeouts:
  ```bash
  pip install --timeout=600 --retries=3 -e ".[dev]"
  ```
- **PyPI connectivity issues** - documented timeouts during dependency installation
- **Alternative installation strategy** when pip fails:
  ```bash
  # Install core dependencies first
  python -m pip install --upgrade pip setuptools wheel
  pip install --timeout=300 pydantic httpx tiktoken termcolor
  pip install --timeout=300 -e . --no-deps
  pip install --timeout=600 pytest ruff pre-commit
  ```
- **Alternative with uv** (often more reliable):
  ```bash
  # Install uv and core dependencies
  pip install uv
  uv pip install --timeout=300 pydantic httpx tiktoken termcolor
  uv pip install --timeout=300 -e . --no-deps
  uv pip install --timeout=600 pytest ruff pre-commit
  ```
- **Dependency conflicts** - always use clean virtual environment
- **Build failures** - ensure build-essential and development headers on Linux

### Testing in Constrained Environments  
- Use `--ignore=test/agentchat/contrib` to skip contrib tests
- Skip Docker-dependent tests with `-m "not docker"`
- LLM tests require API keys and will be skipped automatically without them
- **Real-time features** require additional audio/websocket dependencies
- **Web browsing tests** may require browser installation (Playwright/Chrome)
- **MCP tests** require MCP server setup for full functionality

### Development Container
- **Dev Container support available** in `.devcontainer/`
- Pre-configured with Python 3.10, Quarto, and all build dependencies
- Use "Dev Containers: Reopen in Container" in VS Code

## Repository Structure

### Key Directories
- `autogen/`: Core framework code
  - `agentchat/`: Agent classes and conversation management
  - `coding/`: Code execution engines
  - `oai/`: OpenAI and LLM client implementations
  - `tools/`: Function calling and tool integration
- `test/`: Comprehensive test suite with LLM/non-LLM separation
- `website/`: Documentation source files and build system
- `scripts/`: Build, test, and development automation scripts
- `notebook/`: Jupyter notebook examples and tutorials

### Important Files
- `pyproject.toml`: Project configuration, dependencies, and build settings
- `OAI_CONFIG_LIST_sample`: Template for LLM API key configuration  
- `.pre-commit-config.yaml`: Code quality automation
- `.github/workflows/`: CI/CD pipeline definitions

## Expected Timing and Resource Requirements
Based on GitHub Actions and repository analysis:
- **Fresh clone setup**: 15-25 minutes with uv, 20-30 minutes with pip (with good network)
- **Core dependency installation**: 8-15 minutes with uv, 15-25 minutes with pip
- **Full dev environment**: 20-35 minutes with uv, 30-45 minutes with pip
- **Core test suite** (`test-core-skip-llm.sh`): 8-15 minutes  
- **Full test suite** (`test-skip-llm.sh`): 20-35 minutes
- **Documentation build**: 10-20 minutes
- **Pre-commit hooks**: 3-8 minutes
- **Clean build from scratch**: 25-40 minutes with uv, 35-50 minutes with pip
- **CI/CD pipeline** (full matrix): 2-4 hours across all OS/Python combinations

### Resource Requirements
- **Python**: 3.10, 3.11, 3.12, or 3.13 (fully supported across all versions)
- **Memory**: 2GB+ recommended for builds and tests
- **Disk**: 1GB+ for full dev environment
- **Network**: Stable connection required for dependency installation
- **Optional**: `uv` package manager for faster dependency management

### Additional Validation Commands
- **Import test** (verify installation):
  ```bash
  python -c "import autogen; print(f'AG2 version: {autogen.__version__}')"
  ```
  
- **Dependency check** (validate core modules):
  ```bash
  python -c "from autogen import ConversableAgent, LLMConfig; print('Core imports OK')"
  ```

- **Docker environment test** (if using containerized execution):
  ```bash
  docker --version && python -c "import docker; print('Docker client OK')"
  ```

- **Optional dependencies verification**:
  ```bash
  python -c "from autogen.tools import *; print('Tools module OK')" 2>/dev/null || echo "Tools require additional deps"
  ```

### Reset Development Environment
```bash
# Clean Python cache and artifacts
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
pip uninstall ag2 autogen -y
pip install -e ".[dev]" --force-reinstall
```

### Network-Constrained Development
When external connectivity is limited:
- Use offline documentation: `website/docs/` contains source files
- Core functionality works without LLM API keys
- Focus on `bash scripts/test-core-skip-llm.sh` for validation

## Development Workflow Best Practices
1. **ALWAYS** create virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install with uv (recommended)**: `uv pip install -e ".[dev]"` (allow 30+ minutes)
   **Or with pip**: `pip install -e ".[dev]"` (allow 45+ minutes)
3. Set up pre-commit: `pre-commit install`
4. **For changes in `autogen/`**: Run `bash scripts/test-core-skip-llm.sh`
5. **For changes in `test/`**: Run specific test files or full suite
6. **For changes in `website/` or docs**: Build documentation to verify
7. **ALWAYS** run `pre-commit run --all-files` before committing
8. **For major changes**: Run full test suite and build documentation
9. Test actual functionality with manual agent scenarios (see validation section)

### Working with Network Constraints
When in environments with limited connectivity:
- Use offline documentation in `website/docs/` directory
- Core functionality works without LLM API keys (tests will skip automatically)
- Focus on core tests: `bash scripts/test-core-skip-llm.sh`
- Use system packages where available: `apt install python3-pytest`
- Consider development container in `.devcontainer/` for pre-configured environment

Remember: **NEVER CANCEL long-running builds or tests**. AG2 has complex dependencies and CI operations can take 20-45 minutes legitimately.