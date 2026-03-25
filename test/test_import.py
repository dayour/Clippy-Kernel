# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0


import importlib
import pkgutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest


@contextmanager
def add_to_sys_path(path: Path | None) -> Iterator[None]:
    if path is None:
        yield
        return

    if not path.exists():
        raise ValueError(f"Path {path} does not exist")

    sys.path.append(str(path))
    try:
        yield
    finally:
        sys.path.remove(str(path))


def list_submodules(module_name: str, *, include_path: Path | None = None, include_root: bool = True) -> list[str]:
    """List all submodules of a given module.

    Args:
        module_name (str): The name of the module to list submodules for.
        include_path (Optional[Path], optional): The path to the module. Defaults to None.
        include_root (bool, optional): Whether to include the root module in the list. Defaults to True.

    Returns:
        list: A list of submodule names.
    """
    with add_to_sys_path(include_path):
        try:
            module = importlib.import_module(module_name)  # nosemgrep
        except Exception:
            return []

        # Get the path of the module. This is necessary to find its submodules.
        module_path = module.__path__

        # Initialize an empty list to store the names of submodules
        submodules = [module_name] if include_root else []

        # Iterate over the submodules in the module's path
        for _, name, ispkg in pkgutil.iter_modules(module_path, prefix=f"{module_name}."):
            # Add the name of each submodule to the list
            submodules.append(name)

            if ispkg:
                submodules.extend(list_submodules(name, include_root=False))

        # Return the list of submodule names
        return submodules


def test_list_submodules() -> None:
    # Specify the name of the module you want to inspect
    module_name = "autogen"

    # Get the list of submodules for the specified module
    submodules = list_submodules(module_name)

    assert len(submodules) > 0
    assert "autogen" in submodules
    assert "autogen.io" in submodules
    assert "autogen.coding.jupyter" in submodules


@pytest.mark.parametrize(
    "code",
    (
        (
            "import autogen; import autogen.llm_config; "
            "assert autogen.LLMConfig is autogen.llm_config.LLMConfig; "
            "assert autogen.ModelClient is autogen.llm_config.ModelClient"
        ),
        (
            "import autogen.llm_config; import autogen; "
            "assert autogen.LLMConfig is autogen.llm_config.LLMConfig; "
            "assert autogen.ModelClient is autogen.llm_config.ModelClient"
        ),
        (
            "from autogen.oai.anthropic import AnthropicLLMConfigEntry; "
            "assert AnthropicLLMConfigEntry.__name__ == 'AnthropicLLMConfigEntry'"
        ),
    ),
)
def test_cold_start_imports_no_circular_import(code: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=False,
    )

    assert result.returncode == 0, result.stderr


# Submodules that require optional dependencies not always installed.
# Failures for these are expected and should be skipped, not treated as regressions.
_OPTIONAL_SUBMODULES = frozenset({
    "autogen.a2a",
    "autogen.ag_ui",
    "autogen.mcp.clippy_mcp",
    "autogen.mcp.mcp_client",
    "autogen.opentelemetry",
    "autogen._website",
})


# todo: we should always run this
@pytest.mark.parametrize("module", list_submodules("autogen"))
def test_submodules(module: str) -> None:
    try:
        importlib.import_module(module)  # nosemgrep
    except (ImportError, NameError):
        if module in _OPTIONAL_SUBMODULES or any(module.startswith(m + ".") for m in _OPTIONAL_SUBMODULES):
            pytest.skip(f"{module} requires an optional dependency that is not installed")
        raise
