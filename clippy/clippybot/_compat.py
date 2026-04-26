from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType


def alias_module(name: str, target: str) -> ModuleType:
    """Register ``name`` as an alias of ``target`` in ``sys.modules``."""
    module = import_module(target)
    sys.modules[name] = module
    return module


def alias_submodules(package_name: str, module_map: dict[str, str]) -> None:
    """Register submodule aliases for a compatibility package."""
    for suffix, target in module_map.items():
        alias_module(f"{package_name}.{suffix}", target)
