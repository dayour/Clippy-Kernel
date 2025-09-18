# AG2 Multi-Agent AI Framework

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

AG2 (formerly AutoGen) is an open-source Python framework for building AI agents and facilitating cooperation among multiple agents. It requires **Python version >= 3.10, < 3.14** and supports complex multi-agent conversation patterns, tool usage, and various LLM integrations.

## Working Effectively

### Environment Setup
- **CRITICAL**: Set up proper Python environment first:
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

### Core Installation and Setup
- Install the framework with development dependencies:
  ```bash
  pip install -e ".[dev]"
  ```
  **TIMEOUT WARNING**: Installation takes 15-25 minutes. NEVER CANCEL. Set timeout to 45+ minutes.
  
- If network timeouts occur (common in constrained environments):
  ```bash
  # Try basic installation first
  pip install -e . --timeout=600
  # Then add dev tools separately
  pip install pytest ruff pre-commit mypy --timeout=300
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
- **Dependency conflicts** - always use clean virtual environment
- **Build failures** - ensure build-essential and development headers on Linux

### Testing in Constrained Environments  
- Use `--ignore=test/agentchat/contrib` to skip contrib tests
- Skip Docker-dependent tests with `-m "not docker"`
- LLM tests require API keys and will be skipped automatically without them

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

## Expected Timing
- **Fresh clone setup**: 20-30 minutes
- **Core test suite**: 8-15 minutes  
- **Full test suite**: 20-35 minutes
- **Documentation build**: 10-20 minutes
- **Pre-commit hooks**: 3-8 minutes
- **Clean build from scratch**: 35-50 minutes

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

## Development Workflow
1. **ALWAYS** create virtual environment and activate it
2. Install with `pip install -e ".[dev]"` (allow 45+ minutes)
3. Set up pre-commit: `pre-commit install`
4. Make changes in focused, small iterations
5. **ALWAYS** run `pre-commit run --all-files` before committing
6. **ALWAYS** run `bash scripts/test-core-skip-llm.sh` for core changes
7. Build and serve documentation for UI/docs changes
8. Test actual functionality with manual agent scenarios

Remember: **NEVER CANCEL long-running builds or tests**. This framework has complex dependencies and builds can legitimately take 20-45 minutes.