#!/usr/bin/env python3
# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

"""
Windows-Clippy-MCP Deployment Script

This script handles the deployment of Windows-Clippy-MCP integration including:
- NPM package management for VSCode extension
- UV Python package management
- Azure Key Vault setup
- MCP server configuration
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional


class WindowsClippyMCPDeployer:
    """Deployment manager for Windows-Clippy-MCP integration."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.vscode_extension_dir = project_root / "vscode-extension"
        self.mcp_server_dir = project_root / "mcp-servers"
        self.config_dir = project_root / "config"
        
    def check_dependencies(self) -> bool:
        """Check if required tools are available."""
        required_tools = ["npm", "uv", "python"]
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, "--version"], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"Missing required tools: {', '.join(missing_tools)}")
            print("Please install the missing tools and try again.")
            return False
        
        return True
    
    def setup_python_environment(self, use_uv: bool = True) -> bool:
        """Set up Python environment using UV or pip."""
        try:
            if use_uv:
                print("Setting up Python environment with UV...")
                # Check if uv is available
                subprocess.run(["uv", "--version"], check=True, capture_output=True)
                
                # Install AG2 with Windows-Clippy-MCP support
                subprocess.run([
                    "uv", "pip", "install", "-e", ".[windows-clippy-mcp]"
                ], cwd=self.project_root, check=True)
                
                print("✓ Python environment set up with UV")
            else:
                print("Setting up Python environment with pip...")
                subprocess.run([
                    "pip", "install", "-e", ".[windows-clippy-mcp]"
                ], cwd=self.project_root, check=True)
                
                print("✓ Python environment set up with pip")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error setting up Python environment: {e}")
            return False
        except FileNotFoundError:
            if use_uv:
                print("UV not found, falling back to pip...")
                return self.setup_python_environment(use_uv=False)
            else:
                print("pip not found. Please install Python and pip.")
                return False
    
    def setup_vscode_extension(self) -> bool:
        """Set up the VSCode extension using NPM."""
        try:
            print("Setting up VSCode extension...")
            
            # Create extension directory if it doesn't exist
            self.vscode_extension_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate VSCode extension files
            from autogen.mcp.clippy_mcp import ClippyMCPConfig, create_vscode_extension_files
            
            # Create a default configuration
            config = ClippyMCPConfig(
                clippy_executable_path="windows-clippy-mcp",
                server_name="ag2-windows-clippy",
                vscode_extension_enabled=True,
                vscode_extension_port=8765
            )
            
            create_vscode_extension_files(config, self.vscode_extension_dir)
            
            # Install NPM dependencies
            subprocess.run(["npm", "install"], 
                         cwd=self.vscode_extension_dir, check=True)
            
            # Compile TypeScript
            subprocess.run(["npm", "run", "compile"], 
                         cwd=self.vscode_extension_dir, check=True)
            
            print("✓ VSCode extension set up successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error setting up VSCode extension: {e}")
            return False
        except ImportError as e:
            print(f"Error importing AG2 modules: {e}")
            print("Please ensure AG2 is properly installed with MCP support.")
            return False
    
    def setup_mcp_server(self, port: int = 8765) -> bool:
        """Set up the AG2 MCP server."""
        try:
            print("Setting up AG2 MCP server...")
            
            # Create MCP server directory
            self.mcp_server_dir.mkdir(parents=True, exist_ok=True)
            
            # Create server startup script
            server_script = self.mcp_server_dir / "start_ag2_server.py"
            server_script_content = f'''#!/usr/bin/env python3
"""
AG2 MCP Server Startup Script
"""

import asyncio
import sys
from pathlib import Path

# Add AG2 to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from autogen.mcp.ag2_mcp_server import AG2MCPServer

async def main():
    server = AG2MCPServer("ag2-windows-clippy-server")
    
    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        print("Starting AG2 MCP server with SSE transport on port {port}...")
        await server.run_sse(port={port})
    else:
        print("Starting AG2 MCP server with stdio transport...")
        await server.run_stdio()

if __name__ == "__main__":
    asyncio.run(main())
'''
            
            with open(server_script, "w") as f:
                f.write(server_script_content)
            
            # Make script executable
            server_script.chmod(0o755)
            
            # Create configuration file
            config_file = self.config_dir / "clippy_mcp_config.json"
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                "server_name": "ag2-windows-clippy",
                "clippy_executable_path": "windows-clippy-mcp",
                "vscode_extension_enabled": True,
                "vscode_extension_port": port,
                "memory_engine_enabled": True,
                "shared_llm_keys": {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY"
                }
            }
            
            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=2)
            
            print("✓ AG2 MCP server set up successfully")
            print(f"  - Server script: {server_script}")
            print(f"  - Configuration: {config_file}")
            return True
            
        except Exception as e:
            print(f"Error setting up MCP server: {e}")
            return False
    
    def setup_azure_integration(self, 
                              tenant_id: Optional[str] = None,
                              client_id: Optional[str] = None,
                              vault_url: Optional[str] = None) -> bool:
        """Set up Azure Key Vault and Entra ID integration."""
        try:
            print("Setting up Azure integration...")
            
            # Create Azure configuration template
            azure_config = {
                "entra_id": {
                    "tenant_id": tenant_id or "YOUR_TENANT_ID",
                    "client_id": client_id or "YOUR_CLIENT_ID",
                    "client_secret_env": "AZURE_CLIENT_SECRET",
                    "scopes": ["https://graph.microsoft.com/.default"]
                },
                "azure_key_vault": {
                    "vault_url": vault_url or "https://your-vault.vault.azure.net/",
                    "tenant_id": tenant_id or "YOUR_TENANT_ID",
                    "client_id": client_id or "YOUR_CLIENT_ID",
                    "use_managed_identity": False
                },
                "llm_key_vault_mapping": {
                    "openai": "openai-api-key",
                    "anthropic": "anthropic-api-key",
                    "azure-openai": "azure-openai-api-key"
                }
            }
            
            azure_config_file = self.config_dir / "azure_config.json"
            with open(azure_config_file, "w") as f:
                json.dump(azure_config, f, indent=2)
            
            # Create environment template
            env_template = self.config_dir / ".env.template"
            env_content = """# Azure Configuration
AZURE_TENANT_ID=your_tenant_id_here
AZURE_CLIENT_ID=your_client_id_here
AZURE_CLIENT_SECRET=your_client_secret_here
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/

# LLM API Keys (optional - can be stored in Key Vault instead)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here
"""
            
            with open(env_template, "w") as f:
                f.write(env_content)
            
            print("✓ Azure integration templates created")
            print(f"  - Configuration: {azure_config_file}")
            print(f"  - Environment template: {env_template}")
            print("  Please update these files with your Azure credentials.")
            return True
            
        except Exception as e:
            print(f"Error setting up Azure integration: {e}")
            return False
    
    def create_deployment_scripts(self) -> bool:
        """Create deployment scripts for different platforms."""
        try:
            scripts_dir = self.project_root / "scripts" / "windows-clippy-mcp"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Windows batch script
            windows_script = scripts_dir / "deploy.bat"
            windows_content = '''@echo off
echo Deploying Windows-Clippy-MCP integration...

REM Check if UV is available, fallback to pip
uv --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Using UV for Python package management...
    uv pip install -e .[windows-clippy-mcp]
) else (
    echo Using pip for Python package management...
    pip install -e .[windows-clippy-mcp]
)

REM Set up VSCode extension
cd vscode-extension
npm install
npm run compile

echo Deployment completed!
echo.
echo Next steps:
echo 1. Update config/azure_config.json with your Azure credentials
echo 2. Install the VSCode extension from vscode-extension directory
echo 3. Start the MCP server: python mcp-servers/start_ag2_server.py
'''
            
            with open(windows_script, "w") as f:
                f.write(windows_content)
            
            # Unix shell script
            unix_script = scripts_dir / "deploy.sh"
            unix_content = '''#!/bin/bash
set -e

echo "Deploying Windows-Clippy-MCP integration..."

# Check if UV is available, fallback to pip
if command -v uv &> /dev/null; then
    echo "Using UV for Python package management..."
    uv pip install -e .[windows-clippy-mcp]
else
    echo "Using pip for Python package management..."
    pip install -e .[windows-clippy-mcp]
fi

# Set up VSCode extension
cd vscode-extension
npm install
npm run compile

echo "Deployment completed!"
echo ""
echo "Next steps:"
echo "1. Update config/azure_config.json with your Azure credentials"
echo "2. Install the VSCode extension from vscode-extension directory"
echo "3. Start the MCP server: python mcp-servers/start_ag2_server.py"
'''
            
            with open(unix_script, "w") as f:
                f.write(unix_content)
            
            # Make Unix script executable
            unix_script.chmod(0o755)
            
            print("✓ Deployment scripts created")
            print(f"  - Windows: {windows_script}")
            print(f"  - Unix/Linux/macOS: {unix_script}")
            return True
            
        except Exception as e:
            print(f"Error creating deployment scripts: {e}")
            return False
    
    def deploy(self, 
               use_uv: bool = True,
               setup_vscode: bool = True,
               setup_azure: bool = True,
               mcp_port: int = 8765) -> bool:
        """Run the complete deployment process."""
        print("🚀 Starting Windows-Clippy-MCP deployment...")
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Set up Python environment
        if not self.setup_python_environment(use_uv=use_uv):
            return False
        
        # Set up MCP server
        if not self.setup_mcp_server(port=mcp_port):
            return False
        
        # Set up VSCode extension
        if setup_vscode and not self.setup_vscode_extension():
            return False
        
        # Set up Azure integration
        if setup_azure and not self.setup_azure_integration():
            return False
        
        # Create deployment scripts
        if not self.create_deployment_scripts():
            return False
        
        print("\n🎉 Windows-Clippy-MCP deployment completed successfully!")
        print("\nNext steps:")
        print("1. Update configuration files in the 'config' directory")
        print("2. Install the VSCode extension from 'vscode-extension' directory")
        print("3. Start the MCP server with the appropriate transport")
        print("4. Configure your MCP clients to connect to the server")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Deploy Windows-Clippy-MCP integration")
    parser.add_argument("--no-uv", action="store_true", 
                       help="Use pip instead of UV for Python packages")
    parser.add_argument("--no-vscode", action="store_true",
                       help="Skip VSCode extension setup")
    parser.add_argument("--no-azure", action="store_true",
                       help="Skip Azure integration setup")
    parser.add_argument("--port", type=int, default=8765,
                       help="Port for MCP server (default: 8765)")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory (default: current directory)")
    
    args = parser.parse_args()
    
    deployer = WindowsClippyMCPDeployer(args.project_root)
    
    success = deployer.deploy(
        use_uv=not args.no_uv,
        setup_vscode=not args.no_vscode,
        setup_azure=not args.no_azure,
        mcp_port=args.port
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()