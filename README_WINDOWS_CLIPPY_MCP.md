# 📎 Clippy Kernel Windows-MCP Integration

**Advanced Model Control Protocol integration for Clippy Kernel with enterprise-grade Windows desktop, Azure cloud, and VSCode development environment support.**

This comprehensive integration transforms Clippy Kernel into a powerful desktop assistant and development companion, providing seamless integration with Windows systems, Azure cloud services, and modern development workflows.

## 🚀 Quick Start

### One-Command Deployment
```bash
python scripts/deploy_windows_clippy_mcp.py --full-setup
```

This single command will:
- ✅ Set up Python environment (with UV or pip)
- ✅ Generate complete VSCode extension with TypeScript
- ✅ Configure MCP server for Clippy Kernel tooling
- ✅ Create Azure integration templates and configuration
- ✅ Generate cross-platform deployment scripts
- ✅ Set up agent development team integration
- ✅ Configure real-time collaboration features

### Manual Installation
```bash
# Install with Windows-Clippy-MCP support
pip install -e ".[windows-clippy-mcp,mcp,dev]"

# Or using UV (recommended for faster installation)
uv pip install -e ".[windows-clippy-mcp,mcp,dev]"
```

## 🎯 Key Features Implemented

### 🔐 Enterprise Authentication
- **Azure Key Vault**: Secure LLM API key storage and retrieval
- **Entra ID**: Enterprise identity and access management
- **Managed Identity**: Support for Azure managed identities

### 💻 VSCode Integration
- **Auto-Generated Extension**: Complete TypeScript-based VSCode extension
- **Command Palette**: Native AG2 commands in VSCode
- **Real-time Communication**: WebSocket-based agent communication
- **Configuration UI**: Built-in settings for server and memory options

### 🧠 Memory Engine
- **Agent-Aware Context**: Store and retrieve information with agent-specific context
- **Azure Storage**: Enterprise-grade cloud storage for memory persistence
- **Context Preservation**: Maintain conversation state across sessions

### 🌐 MCP Server
- **Natural Language Interface**: Complete AG2 toolkit accessible via MCP
- **Agent Management**: Create, list, and manage AG2 agents via MCP clients
- **Multi-Agent Orchestration**: Run group chats and agent conversations
- **Code Execution**: Execute code through AG2's secure environments
- **Resource Access**: Expose agents, conversations, and memory as MCP resources

### 📦 Modern Package Management
- **UV Support**: Fast Python package installation and management
- **NPM Integration**: Automated VSCode extension build process
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📁 Files Added

### Core Integration
- [`autogen/mcp/clippy_mcp.py`](autogen/mcp/clippy_mcp.py) - Main integration module
- [`autogen/mcp/ag2_mcp_server.py`](autogen/mcp/ag2_mcp_server.py) - MCP server for AG2 tooling
- [`autogen/mcp/__init__.py`](autogen/mcp/__init__.py) - Updated exports

### Deployment & Automation  
- [`scripts/deploy_windows_clippy_mcp.py`](scripts/deploy_windows_clippy_mcp.py) - Automated deployment script

### Documentation & Examples
- [`notebook/agentchat_windows_clippy_mcp.ipynb`](notebook/agentchat_windows_clippy_mcp.ipynb) - Complete example notebook
- [`website/docs/user-guide/windows-clippy-mcp.md`](website/docs/user-guide/windows-clippy-mcp.md) - Full documentation

### Testing
- [`test/mcp/test_windows_clippy_mcp.py`](test/mcp/test_windows_clippy_mcp.py) - Comprehensive test suite

### Configuration
- [`pyproject.toml`](pyproject.toml) - Added `windows-clippy-mcp` optional dependencies

## 🔧 Usage Examples

### Basic Setup
```python
from autogen.mcp.clippy_mcp import ClippyMCPConfig, create_clippy_toolkit

# Create configuration
config = ClippyMCPConfig(
    clippy_executable_path="windows-clippy-mcp",
    server_name="my-clippy-server",
    vscode_extension_enabled=True,
    memory_engine_enabled=True
)

# Create toolkit with Windows-Clippy-MCP integration
toolkit = await create_clippy_toolkit(config)
```

### Enterprise Configuration with Azure
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

### VSCode Extension Generation
```python
from autogen.mcp.clippy_mcp import create_vscode_extension_files
from pathlib import Path

# Generate complete VSCode extension
create_vscode_extension_files(config, Path("./vscode-extension"))

# Build and install
# cd vscode-extension && npm install && npm run compile
```

### MCP Server Usage
```bash
# Start MCP server with SSE transport (for VSCode)
python autogen/mcp/ag2_mcp_server.py sse --port 8765

# Start with stdio transport (for CLI clients)  
python autogen/mcp/ag2_mcp_server.py stdio
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
pytest test/mcp/test_windows_clippy_mcp.py -v
```

## 🌟 Integration Benefits

### For Developers
- **Native IDE Support**: AG2 agents directly in VSCode
- **Streamlined Workflow**: Natural language commands for complex operations
- **Context Preservation**: Memory engine maintains project context
- **Secure Credentials**: Enterprise-grade API key management

### For Enterprises
- **Azure Integration**: Seamless integration with existing Azure infrastructure
- **Identity Management**: Entra ID support for user authentication
- **Compliance**: Secure credential storage in Azure Key Vault
- **Scalability**: Support for multiple agents and concurrent operations

### For the AG2 Ecosystem
- **MCP Compatibility**: Works with Claude Desktop, Cody, and other MCP clients
- **Extensible Architecture**: Easy to add new Windows-specific capabilities
- **Standard Protocols**: Uses industry-standard MCP for interoperability
- **Modern Tooling**: Supports latest package managers (UV) and build tools

## 🔗 Related Projects

This integration connects AG2 with:
- [Windows-Clippy-MCP](https://github.com/dayour/Windows-Clippy-MCP) - The core Windows desktop assistant
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standard for AI tool integration
- [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/) - Secure credential storage
- [VSCode Extension API](https://code.visualstudio.com/api) - IDE integration framework

## 📋 Next Steps

1. **Install Windows-Clippy-MCP**: Get the core server from the [repository](https://github.com/dayour/Windows-Clippy-MCP)
2. **Run Deployment**: Execute `python scripts/deploy_windows_clippy_mcp.py`
3. **Configure Azure**: Set up Key Vault and Entra ID credentials (optional)
4. **Install VSCode Extension**: Build and install the generated extension
5. **Start Building**: Create AG2 agents with Windows-Clippy-MCP integration!

## 💡 Contributing

This integration follows AG2's development patterns and is fully tested. To contribute:
1. Install with dev dependencies: `pip install -e ".[dev,windows-clippy-mcp]"`
2. Run tests: `pytest test/mcp/test_windows_clippy_mcp.py`
3. Follow existing code patterns and add comprehensive tests
4. Update documentation for any new features

---

*This integration brings the power of AG2's multi-agent framework to Windows desktops with enterprise-grade security and modern development tools. Get started today and experience the future of AI-assisted development!*