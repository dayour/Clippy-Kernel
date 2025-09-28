# Windows-Clippy-MCP Integration

The Windows-Clippy-MCP integration brings enterprise-grade Windows desktop assistant capabilities to AG2, providing seamless integration with VSCode, Azure services, and natural language interfaces for development workflows.

## Overview

This integration connects AG2 with [Windows-Clippy-MCP](https://github.com/dayour/Windows-Clippy-MCP) to provide:

- **VSCode Extension**: Native IDE integration for AG2 agents
- **Azure Key Vault**: Secure API key and credential management
- **Entra ID Authentication**: Enterprise identity integration
- **Memory Engine**: Agent-aware context persistence
- **Natural Language Interface**: MCP server exposing full AG2 tooling
- **NPM/UV Deployment**: Modern package management support

## Prerequisites

Before using the Windows-Clippy-MCP integration, ensure you have:

### Required Dependencies

Install AG2 with Windows-Clippy-MCP support:

```bash
# Using pip
pip install -e ".[windows-clippy-mcp]"

# Using UV (recommended)
uv pip install -e ".[windows-clippy-mcp]"
```

### Optional Azure Setup

For enterprise features, configure:

- **Azure Tenant ID**: Your organization's Azure AD tenant
- **Application Registration**: Client ID and secret for authentication
- **Key Vault**: For secure API key storage
- **Permissions**: Appropriate access to Key Vault and Graph API

## Quick Start

### 1. Automated Deployment

Use the deployment script for a complete setup:

```bash
python scripts/deploy_windows_clippy_mcp.py
```

This will:
- Set up the Python environment with required dependencies
- Generate VSCode extension files
- Create MCP server configuration
- Set up Azure integration templates
- Create deployment scripts for different platforms

### 2. Manual Configuration

Create a configuration for your Windows-Clippy-MCP integration:

```python
from autogen.mcp.clippy_mcp import (
    ClippyMCPConfig, 
    AzureKeyVaultConfig, 
    EntraIDConfig
)

# Basic configuration
config = ClippyMCPConfig(
    server_name="my-clippy-server",
    clippy_executable_path="path/to/windows-clippy-mcp",
    vscode_extension_enabled=True,
    memory_engine_enabled=True
)

# With Azure integration
azure_config = ClippyMCPConfig(
    server_name="enterprise-clippy",
    clippy_executable_path="windows-clippy-mcp",
    
    # Azure Key Vault configuration
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
    
    # LLM API key management
    llm_key_vault_mapping={
        "openai": "openai-api-key-secret",
        "anthropic": "anthropic-api-key-secret"
    }
)
```

### 3. Create Agents with Windows-Clippy-MCP

```python
import asyncio
from autogen import ConversableAgent, LLMConfig
from autogen.mcp.clippy_mcp import create_clippy_toolkit

async def setup_clippy_agents():
    # Create toolkit with Windows-Clippy-MCP integration
    toolkit = await create_clippy_toolkit(
        config=config,
        use_mcp_tools=True,
        use_mcp_resources=True
    )
    
    # Create Clippy assistant agent
    clippy_agent = ConversableAgent(
        name="ClippyAssistant",
        system_message="You are Clippy, integrated with Windows and AG2...",
        llm_config=LLMConfig({"model": "gpt-4"}),
        human_input_mode="NEVER"
    )
    
    # Register Windows-Clippy-MCP tools
    toolkit.register_for_llm(clippy_agent)
    toolkit.register_for_execution(clippy_agent)
    
    return clippy_agent, toolkit

# Run the setup
clippy_agent, toolkit = await setup_clippy_agents()
```

## VSCode Extension

### Installation

The integration includes a VSCode extension for seamless IDE integration:

1. **Generate Extension Files**:
   ```python
   from autogen.mcp.clippy_mcp import create_vscode_extension_files
   
   create_vscode_extension_files(config, Path("./vscode-extension"))
   ```

2. **Build Extension**:
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   ```

3. **Install in VSCode**:
   - Open VSCode
   - Use "Developer: Install Extension from Location"
   - Select the `vscode-extension` directory

### Usage

Once installed, the extension provides:

- **Command Palette**:
  - `AG2 Clippy: Start Assistant` - Start the Clippy assistant
  - `AG2 Clippy: Stop Assistant` - Stop the assistant
  - `AG2 Clippy: Configure` - Open configuration settings

- **Settings**:
  - `ag2-clippy.serverPort`: MCP server port (default: 8765)
  - `ag2-clippy.enableMemoryEngine`: Enable context persistence

## Azure Integration

### Key Vault Setup

Store LLM API keys securely in Azure Key Vault:

```python
# Configure Key Vault integration
azure_kv = AzureKeyVaultConfig(
    vault_url="https://your-vault.vault.azure.net/",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    use_managed_identity=False  # Set to True for managed identity
)

# Map LLM services to Key Vault secrets
llm_mapping = {
    "openai": "openai-api-key",
    "anthropic": "anthropic-api-key",
    "azure-openai": "azure-openai-api-key"
}
```

### Entra ID Authentication

Configure enterprise authentication:

```python
entra_config = EntraIDConfig(
    tenant_id="your-tenant-id",
    client_id="your-app-client-id",
    client_secret="your-client-secret",
    scopes=["https://graph.microsoft.com/.default"]
)
```

### Environment Variables

Set up authentication via environment variables:

```bash
# Azure configuration
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_KEY_VAULT_URL="https://your-vault.vault.azure.net/"

# LLM API keys (optional if using Key Vault)
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## MCP Server

### Starting the Server

The integration includes an MCP server that exposes AG2 functionality:

```bash
# Start with SSE transport (recommended for VSCode)
python autogen/mcp/ag2_mcp_server.py sse --port 8765

# Start with stdio transport (for command-line clients)
python autogen/mcp/ag2_mcp_server.py stdio
```

### Available Tools

The MCP server provides these tools to clients:

- **`create_agent`**: Create new AG2 conversable agents
- **`list_agents`**: List all available agents
- **`send_message`**: Send messages to agents or between agents
- **`run_group_chat`**: Execute multi-agent conversations
- **`execute_code`**: Run code using AG2's execution environment
- **`save_memory`**: Store content in the memory engine
- **`retrieve_memory`**: Retrieve stored content

### Resources

Access AG2 resources via MCP:

- **`ag2://agents`**: Information about created agents
- **`ag2://conversations`**: Chat logs and conversation history
- **`ag2://memory`**: Stored memory content

## Memory Engine

### Saving Context

Store information with agent-specific context:

```python
# Via agent tools (if toolkit is registered)
result = await agent.a_send_message({
    "content": "save_to_memory",
    "args": {
        "content": "Important project information",
        "context": "project_alpha",
        "agent_id": "ClippyAssistant"
    }
})

# Via direct client access
client = WindowsClippyMCPClient(config)
await client.save_memory("project_info", {
    "status": "in_progress",
    "team_members": ["Alice", "Bob"],
    "deadline": "2024-03-01"
})
```

### Retrieving Context

Access stored information:

```python
# Retrieve from memory
memory_content = await client.retrieve_memory("project_info")
print(memory_content)
```

## Configuration Options

### ClippyMCPConfig

Complete configuration options:

```python
config = ClippyMCPConfig(
    # Required
    server_name="my-clippy-server",
    clippy_executable_path="/path/to/windows-clippy-mcp",
    
    # Optional paths and environment
    working_directory="/tmp/clippy-work",
    environment_variables={"DEBUG": "1"},
    
    # Azure integrations
    azure_key_vault=azure_kv_config,
    entra_id=entra_id_config,
    
    # LLM management
    shared_llm_keys={"openai": "sk-..."},
    llm_key_vault_mapping={"openai": "openai-secret"},
    
    # VSCode extension
    vscode_extension_enabled=True,
    vscode_extension_port=8765,
    
    # Memory engine
    memory_engine_enabled=True,
    memory_storage_type="azure"  # or "local"
)
```

## Deployment Scripts

### Cross-Platform Support

The integration includes deployment scripts for different platforms:

**Windows (deploy.bat)**:
```batch
@echo off
uv pip install -e .[windows-clippy-mcp]
cd vscode-extension && npm install && npm run compile
```

**Unix/Linux/macOS (deploy.sh)**:
```bash
#!/bin/bash
uv pip install -e .[windows-clippy-mcp]
cd vscode-extension && npm install && npm run compile
```

### Deployment Options

```bash
# Full deployment with all features
python scripts/deploy_windows_clippy_mcp.py

# Deployment options
python scripts/deploy_windows_clippy_mcp.py \
    --no-uv \           # Use pip instead of UV
    --no-vscode \       # Skip VSCode extension
    --no-azure \        # Skip Azure integration
    --port 9000         # Custom MCP server port
```

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**:
   - Ensure Windows-Clippy-MCP server is installed and running
   - Check that the executable path is correct
   - Verify network connectivity to the MCP server

2. **Azure Authentication Errors**:
   - Verify tenant ID, client ID, and client secret
   - Check application permissions in Azure AD
   - Ensure Key Vault access policies are configured

3. **VSCode Extension Not Loading**:
   - Verify extension files were generated correctly
   - Check that TypeScript compilation succeeded
   - Review VSCode extension logs for errors

4. **Memory Engine Issues**:
   - Check Azure storage account permissions (if using Azure storage)
   - Verify network connectivity to storage services
   - Review memory engine configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
os.environ["DEBUG"] = "1"
```

### Testing the Integration

Run the test suite:

```bash
# Run all Windows-Clippy-MCP tests
pytest test/mcp/test_windows_clippy_mcp.py

# Run with verbose output
pytest test/mcp/test_windows_clippy_mcp.py -v
```

## Examples

See the complete example notebook: [`agentchat_windows_clippy_mcp.ipynb`](../notebook/agentchat_windows_clippy_mcp.ipynb)

## Contributing

To contribute to the Windows-Clippy-MCP integration:

1. Follow the standard AG2 development setup
2. Install Windows-Clippy-MCP dependencies: `pip install -e ".[windows-clippy-mcp]"`
3. Run tests: `pytest test/mcp/test_windows_clippy_mcp.py`
4. Submit pull requests with comprehensive tests and documentation

## Support

For issues specific to Windows-Clippy-MCP integration:
- Check the [Windows-Clippy-MCP repository](https://github.com/dayour/Windows-Clippy-MCP)
- Review AG2 MCP documentation
- Open issues in the appropriate repository with detailed reproduction steps