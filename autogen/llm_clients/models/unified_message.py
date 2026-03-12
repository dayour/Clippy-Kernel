# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

"""
Unified message format supporting all provider features.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .content_blocks import (
    BaseContent,
    CitationContent,
    ContentBlock,
    ReasoningContent,
    ToolCallContent,
)


class UserRoleEnum(str, Enum):
    """Standard message roles with strict typing."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


# Union type: strict typing for known roles, flexible string for unknown
UserRoleType = UserRoleEnum | str


def normalize_role(role: str | None) -> UserRoleType:
    """
    Normalize role string to UserRoleEnum for known roles, or return as-is for unknown roles.
    """
    if not role:
        return UserRoleEnum.ASSISTANT  # Default fallback

    role_mapping = {
        "user": UserRoleEnum.USER,
        "assistant": UserRoleEnum.ASSISTANT,
        "system": UserRoleEnum.SYSTEM,
        "tool": UserRoleEnum.TOOL,
    }

    return role_mapping.get(role.lower(), role)


class UnifiedMessage(BaseModel):
    """Unified message format supporting all provider features."""

    role: UserRoleType
    content: list[ContentBlock]

    name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_text(self) -> str:
        """Extract all text content as string."""
        text_parts = []
        for block in self.content:
            block_text = block.get_text()
            if block_text:
                text_parts.append(block_text)

        return " ".join(text_parts)

    def get_reasoning(self) -> list[ReasoningContent]:
        """Extract reasoning blocks."""
        return [b for b in self.content if isinstance(b, ReasoningContent)]

    def get_citations(self) -> list[CitationContent]:
        """Extract citations."""
        return [b for b in self.content if isinstance(b, CitationContent)]

    def get_tool_calls(self) -> list[ToolCallContent]:
        """Extract tool calls."""
        return [b for b in self.content if isinstance(b, ToolCallContent)]

    def get_content_by_type(self, content_type: str) -> list[BaseContent]:
        """Get all content blocks of a specific type."""
        return [b for b in self.content if b.type == content_type]

    def is_standard_role(self) -> bool:
        """Check if this message uses a standard role."""
        if isinstance(self.role, UserRoleEnum):
            return True
        return self.role in [e.value for e in UserRoleEnum]
