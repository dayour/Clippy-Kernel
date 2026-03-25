# clippy kernel Windows-MCP Integration

This document summarizes the Windows/MCP integration assets that exist in this repository today.

It is an operational setup note, not a claim that the repository provides a turnkey Windows automation product.

## Quick Start

### Default Deployment
```bash
python scripts/deploy_windows_clippy_mcp.py
```

This command runs the default deployment flow and will:
- set up the Python environment (with UV or pip)
- generate the VSCode extension scaffold
- configure MCP server support for clippy kernel tooling
- create Azure integration templates and configuration
- generate deployment assets
- create local `vscode-extension/`, `mcp-servers/`, and `config/` artifacts

### Manual Installation
```bash
# Install the Windows/MCP integration surface only
pip install -e ".[windows-clippy-mcp]"

# Install the CLI plus Windows/MCP-related extras
pip install -e ".[mcp-proxy-gen,windows-clippy-mcp,mcp,dev]"

# Or using UV
uv pip install -e ".[windows-clippy-mcp]"
uv pip install -e ".[mcp-proxy-gen,windows-clippy-mcp,mcp,dev]"
```

```bash
# The deployment script itself currently installs:
uv pip install -e ".[mcp-proxy-gen,windows-clippy-mcp,mcp,dev]"
```

If you only need the Python integration modules and not the `clippy-swe` CLI, `mcp-proxy-gen` is optional.

## Implemented areas

### Authentication options
- Azure Key Vault for secret retrieval
- Entra ID integration points
- Managed identity support

### VSCode Integration
- Generated VS Code extension scaffolding
- Command-palette integration points
- WebSocket-based communication
- Extension configuration UI

### Memory Engine
- Agent-aware memory abstractions
- Azure storage integration points
- Session context persistence hooks

### MCP Server
- AG2 toolkit exposure over MCP
- Agent-management operations
- Multi-agent orchestration entry points
- Code-execution hooks
- MCP resources for agents, conversations, and memory

### Tooling
- `uv`-based Python installation support
- npm-based VS Code extension build steps
- cross-platform packaging where dependencies are available

## Relevant files

### Core Integration
- [`autogen/mcp/clippy_mcp.py`](autogen/mcp/clippy_mcp.py) - Main integration module
- [`autogen/mcp/ag2_mcp_server.py`](autogen/mcp/ag2_mcp_server.py) - MCP server for AG2 tooling
- [`autogen/mcp/__init__.py`](autogen/mcp/__init__.py) - Updated exports

### Deployment and Automation
- [`scripts/deploy_windows_clippy_mcp.py`](scripts/deploy_windows_clippy_mcp.py) - Automated deployment script

### Documentation and Examples
- [`notebook/agentchat_windows_clippy_mcp.ipynb`](notebook/agentchat_windows_clippy_mcp.ipynb) - Complete example notebook
- [`website/docs/user-guide/windows-clippy-mcp.md`](website/docs/user-guide/windows-clippy-mcp.md) - Full documentation

### Testing
- [`test/mcp/test_windows_clippy_mcp.py`](test/mcp/test_windows_clippy_mcp.py) - Comprehensive test suite

### Configuration
- [`pyproject.toml`](pyproject.toml) - Added `windows-clippy-mcp` optional dependencies

## Usage examples

### Basic Setup
```python
import asyncio

from autogen.mcp.clippy_mcp import ClippyMCPConfig, create_clippy_toolkit

config = ClippyMCPConfig(
    clippy_executable_path="windows-clippy-mcp",
    server_name="my-clippy-server",
    vscode_extension_enabled=True
)

async def main() -> None:
    toolkit = await create_clippy_toolkit(config)
    print(len(toolkit.tools))

asyncio.run(main())
```

### Azure-backed configuration
```python
from autogen.mcp.clippy_mcp import (
    ClippyMCPConfig, AzureKeyVaultConfig, EntraIDConfig
)

config = ClippyMCPConfig(
    clippy_executable_path="windows-clippy-mcp",
    
    # Azure Key Vault for secure API key storage
    azure_key_vault=AzureKeyVaultConfig(
        vault_url="https://your-vault.vault.azure.net/",
        tenant_id="your-tenant-id",
        client_id="your-client-id"
    ),
    
    # Entra ID authentication
    entra_id=EntraIDConfig(
        tenant_id="your-tenant-id",
        client_id="your-client-id",
        client_secret="your-client-secret"
    ),
    
    # Map LLM services to Key Vault secrets
    llm_key_vault_mapping={
        "openai": "openai-api-key-secret",
        "anthropic": "anthropic-api-key-secret"
    }
)
```

### VSCode extension generation
```python
from autogen.mcp.clippy_mcp import create_vscode_extension_files
from pathlib import Path

# Generate complete VSCode extension
create_vscode_extension_files(config, Path("./vscode-extension"))

# Build and install
# cd vscode-extension && npm install && npm run compile
```

### MCP server usage
```bash
# Start MCP server with SSE transport (for VSCode)
python autogen/mcp/ag2_mcp_server.py sse --port 8765

# Start with stdio transport (for CLI clients)  
python autogen/mcp/ag2_mcp_server.py stdio
```

## Testing

Run the repository test module for this surface:
```bash
pytest test/mcp/test_windows_clippy_mcp.py -v
```

This is the main automated evidence for this integration in the repository.

## Operational notes

### What this document is useful for
- locating the relevant Python modules, scripts, docs, and tests
- understanding which extras are usually needed for local setup
- finding example configuration shapes for MCP, Azure, and VS Code integration

### What it does not prove
- that Windows desktop automation is production-ready end to end
- that every Azure or VS Code path is exercised by automated tests in this repo
- that the default deployment script matches every local environment without adjustment

## Related projects

This integration connects AG2 with:
- [Windows-Clippy-MCP](https://github.com/dayour/Windows-Clippy-MCP) - The core Windows desktop assistant
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standard for AI tool integration
- [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/) - Secure credential storage
- [VSCode Extension API](https://code.visualstudio.com/api) - IDE integration framework

## Next steps

1. Install Windows-Clippy-MCP from the [repository](https://github.com/dayour/Windows-Clippy-MCP) if your workflow needs it.
2. Run `python scripts/deploy_windows_clippy_mcp.py`.
3. Configure Azure credentials only for the features that need them.
4. Build and install the generated VS Code extension if you plan to use that path.
5. Run the test module and any manual checks relevant to your environment.

## Contributing

This integration follows the repository's AG2 patterns. To contribute:
1. Install with dev dependencies: `pip install -e ".[dev,mcp-proxy-gen,windows-clippy-mcp]"`
2. Run tests: `pytest test/mcp/test_windows_clippy_mcp.py`
3. Follow existing code patterns and add comprehensive tests
4. Update documentation for any new features

---

Use the code, tests, and the main user guide under `website/docs/user-guide/windows-clippy-mcp.md` as the source of truth when this summary and the implementation diverge.
