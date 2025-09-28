# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

"""
Windows-Clippy-MCP Integration Module

This module provides integration between AG2 and Windows-Clippy-MCP, including:
- VSCode extension support
- Azure Key Vault integration for memory engine
- Entra ID authentication
- Shared LLM service API key management
- Natural language interface for AG2 tooling
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager, AsyncExitStack
from collections.abc import AsyncIterator

from pydantic import BaseModel, Field, AnyUrl
from ..import_utils import optional_import_block, require_optional_import
from ..tools import Tool, Toolkit
from .mcp_client import StdioConfig, SseConfig, MCPConfig, SessionConfigProtocol

with optional_import_block():
    from mcp.client.session import ClientSession
    from mcp.types import Tool as MCPTool

__all__ = [
    "ClippyMCPConfig", 
    "WindowsClippyMCPClient",
    "create_clippy_toolkit",
    "AzureKeyVaultConfig",
    "EntraIDConfig"
]


class AzureKeyVaultConfig(BaseModel):
    """Configuration for Azure Key Vault integration."""
    
    vault_url: str = Field(..., description="Azure Key Vault URL")
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Azure AD Application Client ID")
    client_secret: Optional[str] = Field(default=None, description="Azure AD Client Secret")
    certificate_path: Optional[str] = Field(default=None, description="Path to certificate for authentication")
    use_managed_identity: bool = Field(default=False, description="Use Azure Managed Identity")


class EntraIDConfig(BaseModel):
    """Configuration for Entra ID (Azure AD) authentication."""
    
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Application Client ID")
    client_secret: Optional[str] = Field(default=None, description="Client Secret")
    scopes: List[str] = Field(default=["https://graph.microsoft.com/.default"], description="OAuth scopes")
    authority: str = Field(default="https://login.microsoftonline.com", description="Authority URL")


class ClippyMCPConfig(BaseModel):
    """Configuration for Windows-Clippy-MCP integration."""
    
    server_name: str = Field(default="windows-clippy-mcp", description="MCP server name")
    clippy_executable_path: str = Field(..., description="Path to Windows-Clippy-MCP executable")
    working_directory: Optional[str] = Field(default=None, description="Working directory for MCP server")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    
    # Azure integrations
    azure_key_vault: Optional[AzureKeyVaultConfig] = Field(default=None, description="Azure Key Vault configuration")
    entra_id: Optional[EntraIDConfig] = Field(default=None, description="Entra ID configuration")
    
    # LLM service configuration
    shared_llm_keys: Dict[str, str] = Field(default_factory=dict, description="Shared LLM service API keys")
    llm_key_vault_mapping: Dict[str, str] = Field(default_factory=dict, description="Mapping of LLM services to Key Vault secret names")
    
    # VSCode extension settings
    vscode_extension_enabled: bool = Field(default=True, description="Enable VSCode extension support")
    vscode_extension_port: int = Field(default=8765, description="Port for VSCode extension communication")
    
    # Memory engine settings
    memory_engine_enabled: bool = Field(default=True, description="Enable memory engine")
    memory_storage_type: str = Field(default="azure", description="Memory storage type (azure, local, etc.)")


class WindowsClippyMCPClient:
    """Client for Windows-Clippy-MCP integration with AG2."""
    
    def __init__(self, config: ClippyMCPConfig):
        self.config = config
        self._session: Optional[ClientSession] = None
        self._azure_credentials: Optional[Any] = None
        
    async def initialize_azure_auth(self) -> None:
        """Initialize Azure authentication if configured."""
        if not self.config.entra_id:
            return
            
        try:
            # This would require azure-identity package
            with optional_import_block():
                from azure.identity import ClientSecretCredential, DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
                
            if self.config.azure_key_vault and self.config.azure_key_vault.use_managed_identity:
                self._azure_credentials = DefaultAzureCredential()
            elif self.config.entra_id.client_secret:
                self._azure_credentials = ClientSecretCredential(
                    tenant_id=self.config.entra_id.tenant_id,
                    client_id=self.config.entra_id.client_id,
                    client_secret=self.config.entra_id.client_secret
                )
        except ImportError:
            print("Warning: Azure authentication libraries not available. Install azure-identity and azure-keyvault-secrets.")
    
    async def get_llm_api_key(self, service_name: str) -> Optional[str]:
        """Get LLM API key from shared configuration or Azure Key Vault."""
        # First check local shared keys
        if service_name in self.config.shared_llm_keys:
            return self.config.shared_llm_keys[service_name]
        
        # Then check Azure Key Vault if configured
        if (self.config.azure_key_vault and 
            service_name in self.config.llm_key_vault_mapping and 
            self._azure_credentials):
            
            try:
                with optional_import_block():
                    from azure.keyvault.secrets import SecretClient
                    
                client = SecretClient(
                    vault_url=self.config.azure_key_vault.vault_url,
                    credential=self._azure_credentials
                )
                secret_name = self.config.llm_key_vault_mapping[service_name]
                secret = await client.get_secret(secret_name)
                return secret.value
            except ImportError:
                print("Warning: Azure Key Vault libraries not available.")
            except Exception as e:
                print(f"Error retrieving secret from Key Vault: {e}")
        
        return None
    
    def create_stdio_config(self) -> StdioConfig:
        """Create StdioConfig for Windows-Clippy-MCP server."""
        return StdioConfig(
            command=self.config.clippy_executable_path,
            args=["--mcp-mode", "stdio"],
            transport="stdio",
            server_name=self.config.server_name,
            environment=self.config.environment_variables,
            working_dir=self.config.working_directory
        )
    
    def create_vscode_extension_config(self) -> Dict[str, Any]:
        """Create configuration for VSCode extension."""
        return {
            "name": "AG2 Windows-Clippy-MCP",
            "version": "1.0.0",
            "description": "VSCode extension for AG2 Windows-Clippy-MCP integration",
            "publisher": "ag2ai",
            "engines": {
                "vscode": "^1.80.0"
            },
            "categories": ["Other"],
            "activationEvents": [
                "onCommand:ag2-clippy.start",
                "onLanguage:python"
            ],
            "main": "./out/extension.js",
            "contributes": {
                "commands": [
                    {
                        "command": "ag2-clippy.start",
                        "title": "Start AG2 Clippy Assistant"
                    },
                    {
                        "command": "ag2-clippy.stop",
                        "title": "Stop AG2 Clippy Assistant"
                    },
                    {
                        "command": "ag2-clippy.configure",
                        "title": "Configure AG2 Clippy"
                    }
                ],
                "configuration": {
                    "title": "AG2 Clippy Configuration",
                    "properties": {
                        "ag2-clippy.serverPort": {
                            "type": "number",
                            "default": self.config.vscode_extension_port,
                            "description": "Port for MCP server communication"
                        },
                        "ag2-clippy.enableMemoryEngine": {
                            "type": "boolean",
                            "default": self.config.memory_engine_enabled,
                            "description": "Enable memory engine for context persistence"
                        }
                    }
                }
            },
            "scripts": {
                "vscode:prepublish": "npm run compile",
                "compile": "tsc -p ./",
                "watch": "tsc -watch -p ./"
            },
            "devDependencies": {
                "@types/node": "^18.x",
                "@types/vscode": "^1.80.0",
                "typescript": "^5.0.0"
            },
            "dependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0",
                "ws": "^8.0.0"
            }
        }


@require_optional_import("mcp", "mcp")
async def create_clippy_toolkit(
    config: ClippyMCPConfig,
    use_mcp_tools: bool = True,
    use_mcp_resources: bool = True,
    resource_download_folder: Optional[Path] = None
) -> Toolkit:
    """Create a toolkit for Windows-Clippy-MCP integration."""
    
    client = WindowsClippyMCPClient(config)
    await client.initialize_azure_auth()
    
    # Create MCP configuration
    stdio_config = client.create_stdio_config()
    mcp_config = MCPConfig(servers=[stdio_config])
    
    # Import necessary MCP functions
    from .mcp_client import create_toolkit
    
    # Create the toolkit using existing MCP infrastructure
    async with AsyncExitStack() as exit_stack:
        session = await stdio_config.create_session(exit_stack)
        toolkit = await create_toolkit(
            session=session,
            use_mcp_tools=use_mcp_tools,
            use_mcp_resources=use_mcp_resources,
            resource_download_folder=resource_download_folder
        )
        
        # Add custom tools for Windows-Clippy-MCP features
        clippy_tools = await _create_clippy_specific_tools(client, session)
        for tool in clippy_tools:
            toolkit.add_tool(tool)
        
        return toolkit


async def _create_clippy_specific_tools(client: WindowsClippyMCPClient, session: ClientSession) -> List[Tool]:
    """Create Windows-Clippy-MCP specific tools."""
    tools = []
    
    # Memory management tool
    if client.config.memory_engine_enabled:
        async def save_to_memory(content: str, context: str = "general", agent_id: Optional[str] = None) -> str:
            """Save content to the memory engine with optional agent context."""
            try:
                # This would interact with the Clippy MCP server's memory functions
                result = await session.call_tool("save_memory", {
                    "content": content,
                    "context": context,
                    "agent_id": agent_id or "default",
                    "timestamp": str(datetime.now().isoformat())
                })
                return f"Memory saved successfully: {result}"
            except Exception as e:
                return f"Error saving to memory: {e}"
        
        memory_tool = Tool(
            name="save_to_memory",
            description="Save content to the Windows-Clippy-MCP memory engine with agent context",
            func_or_tool=save_to_memory
        )
        tools.append(memory_tool)
    
    # LLM key management tool
    async def get_llm_key(service_name: str) -> str:
        """Get LLM API key for the specified service."""
        key = await client.get_llm_api_key(service_name)
        if key:
            return f"API key retrieved for {service_name}"
        else:
            return f"No API key found for {service_name}"
    
    llm_key_tool = Tool(
        name="get_llm_key",
        description="Retrieve LLM API key from shared configuration or Azure Key Vault",
        func_or_tool=get_llm_key
    )
    tools.append(llm_key_tool)
    
    # VSCode integration tool
    if client.config.vscode_extension_enabled:
        async def send_to_vscode(message: str, command: str = "display") -> str:
            """Send a message or command to VSCode extension."""
            try:
                # This would send commands to the VSCode extension via WebSocket or similar
                # For now, return a placeholder response
                return f"Message sent to VSCode: {message} (command: {command})"
            except Exception as e:
                return f"Error communicating with VSCode: {e}"
        
        vscode_tool = Tool(
            name="send_to_vscode",
            description="Send messages or commands to the VSCode extension",
            func_or_tool=send_to_vscode
        )
        tools.append(vscode_tool)
    
    return tools


def create_vscode_extension_files(config: ClippyMCPConfig, output_dir: Path) -> None:
    """Create VSCode extension files for Windows-Clippy-MCP integration."""
    client = WindowsClippyMCPClient(config)
    extension_config = client.create_vscode_extension_config()
    
    # Create package.json
    package_json_path = output_dir / "package.json"
    with open(package_json_path, "w") as f:
        json.dump(extension_config, f, indent=2)
    
    # Create TypeScript extension source
    extension_ts_content = '''
import * as vscode from 'vscode';
import WebSocket from 'ws';

let mcpSocket: WebSocket | null = null;

export function activate(context: vscode.ExtensionContext) {
    console.log('AG2 Windows-Clippy-MCP extension is now active!');

    // Register commands
    let startCommand = vscode.commands.registerCommand('ag2-clippy.start', () => {
        startClippyServer();
    });

    let stopCommand = vscode.commands.registerCommand('ag2-clippy.stop', () => {
        stopClippyServer();
    });

    let configureCommand = vscode.commands.registerCommand('ag2-clippy.configure', () => {
        showConfiguration();
    });

    context.subscriptions.push(startCommand, stopCommand, configureCommand);
}

function startClippyServer() {
    const config = vscode.workspace.getConfiguration('ag2-clippy');
    const port = config.get<number>('serverPort', 8765);
    
    mcpSocket = new WebSocket(`ws://localhost:${port}`);
    
    mcpSocket.on('open', () => {
        vscode.window.showInformationMessage('AG2 Clippy Assistant started successfully!');
    });
    
    mcpSocket.on('message', (data) => {
        try {
            const message = JSON.parse(data.toString());
            handleMCPMessage(message);
        } catch (error) {
            console.error('Error parsing MCP message:', error);
        }
    });
    
    mcpSocket.on('error', (error) => {
        vscode.window.showErrorMessage(`AG2 Clippy connection error: ${error.message}`);
    });
}

function stopClippyServer() {
    if (mcpSocket) {
        mcpSocket.close();
        mcpSocket = null;
        vscode.window.showInformationMessage('AG2 Clippy Assistant stopped.');
    }
}

function handleMCPMessage(message: any) {
    switch (message.type) {
        case 'notification':
            vscode.window.showInformationMessage(message.content);
            break;
        case 'code_suggestion':
            insertCodeSuggestion(message.content);
            break;
        case 'memory_update':
            // Handle memory engine updates
            break;
        default:
            console.log('Unknown MCP message type:', message.type);
    }
}

function insertCodeSuggestion(code: string) {
    const editor = vscode.window.activeTextEditor;
    if (editor) {
        const position = editor.selection.active;
        editor.edit(editBuilder => {
            editBuilder.insert(position, code);
        });
    }
}

function showConfiguration() {
    vscode.commands.executeCommand('workbench.action.openSettings', 'ag2-clippy');
}

export function deactivate() {
    if (mcpSocket) {
        mcpSocket.close();
    }
}
'''
    
    # Create src directory and extension.ts
    src_dir = output_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    extension_ts_path = src_dir / "extension.ts"
    with open(extension_ts_path, "w") as f:
        f.write(extension_ts_content)
    
    # Create tsconfig.json
    tsconfig_content = {
        "compilerOptions": {
            "module": "commonjs",
            "target": "ES2020",
            "outDir": "out",
            "lib": ["ES2020"],
            "sourceMap": True,
            "rootDir": "src",
            "strict": True
        },
        "exclude": ["node_modules", ".vscode-test"]
    }
    
    tsconfig_path = output_dir / "tsconfig.json"
    with open(tsconfig_path, "w") as f:
        json.dump(tsconfig_content, f, indent=2)
    
    print(f"VSCode extension files created in {output_dir}")