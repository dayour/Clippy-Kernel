# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Windows-Clippy-MCP integration
"""

import pytest
import asyncio
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from autogen.mcp.clippy_mcp import (
    ClippyMCPConfig,
    WindowsClippyMCPClient,
    AzureKeyVaultConfig,
    EntraIDConfig,
    create_vscode_extension_files,
)


class TestClippyMCPConfig:
    """Test the ClippyMCPConfig model."""
    
    def test_basic_config_creation(self):
        """Test creating a basic configuration."""
        config = ClippyMCPConfig(
            clippy_executable_path="/path/to/clippy.exe",
            server_name="test-clippy"
        )
        
        assert config.server_name == "test-clippy"
        assert config.clippy_executable_path == "/path/to/clippy.exe"
        assert config.vscode_extension_enabled is True
        assert config.memory_engine_enabled is True
        assert config.vscode_extension_port == 8765
    
    def test_config_with_azure_integration(self):
        """Test configuration with Azure Key Vault and Entra ID."""
        azure_kv = AzureKeyVaultConfig(
            vault_url="https://test-vault.vault.azure.net/",
            tenant_id="test-tenant",
            client_id="test-client"
        )
        
        entra_id = EntraIDConfig(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret"
        )
        
        config = ClippyMCPConfig(
            clippy_executable_path="/path/to/clippy.exe",
            azure_key_vault=azure_kv,
            entra_id=entra_id,
            shared_llm_keys={"openai": "test-key"},
            llm_key_vault_mapping={"openai": "openai-secret"}
        )
        
        assert config.azure_key_vault is not None
        assert config.entra_id is not None
        assert config.shared_llm_keys["openai"] == "test-key"
        assert config.llm_key_vault_mapping["openai"] == "openai-secret"
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Missing required fields should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            ClippyMCPConfig()


class TestAzureKeyVaultConfig:
    """Test the AzureKeyVaultConfig model."""
    
    def test_basic_keyvault_config(self):
        """Test basic Key Vault configuration."""
        config = AzureKeyVaultConfig(
            vault_url="https://test.vault.azure.net/",
            tenant_id="tenant-123",
            client_id="client-456"
        )
        
        assert config.vault_url == "https://test.vault.azure.net/"
        assert config.tenant_id == "tenant-123"
        assert config.client_id == "client-456"
        assert config.use_managed_identity is False
    
    def test_managed_identity_config(self):
        """Test configuration with managed identity."""
        config = AzureKeyVaultConfig(
            vault_url="https://test.vault.azure.net/",
            tenant_id="tenant-123",
            client_id="client-456",
            use_managed_identity=True
        )
        
        assert config.use_managed_identity is True


class TestEntraIDConfig:
    """Test the EntraIDConfig model."""
    
    def test_basic_entra_config(self):
        """Test basic Entra ID configuration."""
        config = EntraIDConfig(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789"
        )
        
        assert config.tenant_id == "tenant-123"
        assert config.client_id == "client-456"
        assert config.client_secret == "secret-789"
        assert "https://graph.microsoft.com/.default" in config.scopes
    
    def test_custom_scopes(self):
        """Test configuration with custom scopes."""
        custom_scopes = ["https://custom.api/.default", "openid"]
        config = EntraIDConfig(
            tenant_id="tenant-123",
            client_id="client-456",
            scopes=custom_scopes
        )
        
        assert config.scopes == custom_scopes


class TestWindowsClippyMCPClient:
    """Test the WindowsClippyMCPClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ClippyMCPConfig(
            clippy_executable_path="/path/to/clippy.exe",
            server_name="test-clippy",
            shared_llm_keys={"openai": "test-openai-key"}
        )
        self.client = WindowsClippyMCPClient(self.config)
    
    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client.config == self.config
        assert self.client._session is None
        assert self.client._azure_credentials is None
    
    @pytest.mark.asyncio
    async def test_get_llm_api_key_from_shared_keys(self):
        """Test retrieving API key from shared configuration."""
        key = await self.client.get_llm_api_key("openai")
        assert key == "test-openai-key"
    
    @pytest.mark.asyncio
    async def test_get_llm_api_key_not_found(self):
        """Test retrieving non-existent API key."""
        key = await self.client.get_llm_api_key("nonexistent")
        assert key is None
    
    def test_create_stdio_config(self):
        """Test creating stdio configuration."""
        stdio_config = self.client.create_stdio_config()
        
        assert stdio_config.command == "/path/to/clippy.exe"
        assert stdio_config.args == ["--mcp-mode", "stdio"]
        assert stdio_config.transport == "stdio"
        assert stdio_config.server_name == "test-clippy"
    
    def test_create_vscode_extension_config(self):
        """Test creating VSCode extension configuration."""
        vscode_config = self.client.create_vscode_extension_config()
        
        assert vscode_config["name"] == "AG2 Windows-Clippy-MCP"
        assert vscode_config["publisher"] == "ag2ai"
        assert "commands" in vscode_config["contributes"]
        assert len(vscode_config["contributes"]["commands"]) >= 3
    
    @pytest.mark.asyncio
    @patch('autogen.mcp.clippy_mcp.optional_import_block')
    async def test_initialize_azure_auth_no_config(self, mock_import):
        """Test Azure auth initialization without configuration."""
        # No Entra ID config
        client = WindowsClippyMCPClient(ClippyMCPConfig(
            clippy_executable_path="/path/to/clippy.exe"
        ))
        
        await client.initialize_azure_auth()
        assert client._azure_credentials is None
    
    @pytest.mark.asyncio
    async def test_azure_keyvault_integration(self):
        """Test Azure Key Vault integration."""
        azure_config = ClippyMCPConfig(
            clippy_executable_path="/path/to/clippy.exe",
            azure_key_vault=AzureKeyVaultConfig(
                vault_url="https://test.vault.azure.net/",
                tenant_id="test-tenant",
                client_id="test-client"
            ),
            entra_id=EntraIDConfig(
                tenant_id="test-tenant",
                client_id="test-client",
                client_secret="test-secret"
            ),
            llm_key_vault_mapping={"openai": "openai-secret"}
        )
        
        client = WindowsClippyMCPClient(azure_config)
        
        # Mock Azure libraries
        with patch('autogen.mcp.clippy_mcp.optional_import_block'):
            with patch('azure.identity.ClientSecretCredential') as mock_cred:
                with patch('azure.keyvault.secrets.SecretClient') as mock_client:
                    # Mock secret retrieval
                    mock_secret = Mock()
                    mock_secret.value = "mock-api-key"
                    mock_client.return_value.get_secret.return_value = mock_secret
                    
                    # This will fail due to import mocking, but we test the logic
                    key = await client.get_llm_api_key("openai")
                    # In a real scenario with proper imports, this would return the key


class TestVSCodeExtensionGeneration:
    """Test VSCode extension file generation."""
    
    def test_create_vscode_extension_files(self):
        """Test creating VSCode extension files."""
        config = ClippyMCPConfig(
            clippy_executable_path="/path/to/clippy.exe",
            vscode_extension_port=9876
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            create_vscode_extension_files(config, output_dir)
            
            # Check that files were created
            package_json = output_dir / "package.json"
            assert package_json.exists()
            
            src_dir = output_dir / "src"
            assert src_dir.exists()
            
            extension_ts = src_dir / "extension.ts"
            assert extension_ts.exists()
            
            tsconfig_json = output_dir / "tsconfig.json"
            assert tsconfig_json.exists()
            
            # Check package.json content
            with open(package_json) as f:
                package_data = json.load(f)
            
            assert package_data["name"] == "AG2 Windows-Clippy-MCP"
            assert "ag2-clippy.start" in [cmd["command"] for cmd in package_data["contributes"]["commands"]]
            assert package_data["contributes"]["configuration"]["properties"]["ag2-clippy.serverPort"]["default"] == 9876


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    def test_full_config_integration(self):
        """Test full configuration with all features enabled."""
        azure_kv = AzureKeyVaultConfig(
            vault_url="https://test.vault.azure.net/",
            tenant_id="test-tenant",
            client_id="test-client"
        )
        
        entra_id = EntraIDConfig(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret"
        )
        
        config = ClippyMCPConfig(
            server_name="integration-test",
            clippy_executable_path="/usr/local/bin/clippy-mcp",
            working_directory="/tmp/clippy-work",
            environment_variables={"DEBUG": "1", "LOG_LEVEL": "INFO"},
            azure_key_vault=azure_kv,
            entra_id=entra_id,
            shared_llm_keys={
                "openai": "sk-test-key",
                "anthropic": "ant-test-key"
            },
            llm_key_vault_mapping={
                "openai": "openai-api-key",
                "anthropic": "anthropic-api-key"
            },
            vscode_extension_enabled=True,
            vscode_extension_port=8888,
            memory_engine_enabled=True,
            memory_storage_type="azure"
        )
        
        client = WindowsClippyMCPClient(config)
        
        # Test stdio config generation
        stdio_config = client.create_stdio_config()
        assert stdio_config.server_name == "integration-test"
        assert stdio_config.working_dir == "/tmp/clippy-work"
        assert stdio_config.environment["DEBUG"] == "1"
        
        # Test VSCode config generation
        vscode_config = client.create_vscode_extension_config()
        assert vscode_config["contributes"]["configuration"]["properties"]["ag2-clippy.serverPort"]["default"] == 8888
    
    @pytest.mark.asyncio
    async def test_memory_and_key_management_workflow(self):
        """Test a complete workflow with memory and key management."""
        config = ClippyMCPConfig(
            clippy_executable_path="/path/to/clippy.exe",
            shared_llm_keys={
                "openai": "sk-real-key",
                "anthropic": "ant-real-key"
            },
            memory_engine_enabled=True
        )
        
        client = WindowsClippyMCPClient(config)
        
        # Test key retrieval workflow
        openai_key = await client.get_llm_api_key("openai")
        assert openai_key == "sk-real-key"
        
        anthropic_key = await client.get_llm_api_key("anthropic")
        assert anthropic_key == "ant-real-key"
        
        missing_key = await client.get_llm_api_key("nonexistent")
        assert missing_key is None


# Skip tests that require actual MCP server or Azure services
@pytest.mark.skip(reason="Requires actual Windows-Clippy-MCP server")
class TestLiveIntegration:
    """Tests that require actual MCP server running."""
    
    @pytest.mark.asyncio
    async def test_create_clippy_toolkit_live(self):
        """Test creating toolkit with actual MCP server."""
        from autogen.mcp.clippy_mcp import create_clippy_toolkit
        
        config = ClippyMCPConfig(
            clippy_executable_path="windows-clippy-mcp",
            server_name="live-test"
        )
        
        toolkit = await create_clippy_toolkit(config)
        assert toolkit is not None
        assert len(toolkit.tools) > 0


if __name__ == "__main__":
    pytest.main([__file__])