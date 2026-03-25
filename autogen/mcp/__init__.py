# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

# clippy kernel enhanced Tools
from ..import_utils import optional_import_block
from .clippy_kernel_tools import (
    ClippyKernelToolkit,
    CloudConfig,
    DatabaseConfig,
    WebScrapingConfig,
    create_clippy_kernel_toolkit,
)

with optional_import_block() as mcp_optional_import:
    from .clippy_mcp import (
        AzureKeyVaultConfig,
        ClippyMCPConfig,
        EntraIDConfig,
        WindowsClippyMCPClient,
        create_clippy_toolkit,
        create_vscode_extension_files,
    )
    from .mcp_client import create_toolkit

__all__ = [
    # clippy kernel tools
    "ClippyKernelToolkit",
    "create_clippy_kernel_toolkit",
    "WebScrapingConfig",
    "DatabaseConfig",
    "CloudConfig",
]

if mcp_optional_import.is_successful:
    __all__.extend(
        [
            "AzureKeyVaultConfig",
            "ClippyMCPConfig",
            "EntraIDConfig",
            "WindowsClippyMCPClient",
            "create_clippy_toolkit",
            "create_toolkit",
            "create_vscode_extension_files",
        ]
    )
