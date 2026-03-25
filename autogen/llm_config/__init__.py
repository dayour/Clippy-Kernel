# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .client import ModelClient

if TYPE_CHECKING:
    from .config import LLMConfig

__all__ = ("LLMConfig", "ModelClient")


def __getattr__(name: str) -> Any:
    if name == "LLMConfig":
        from .config import LLMConfig

        return LLMConfig

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
