# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

"""
Unified response format for all LLM providers.
"""

from typing import Any, ClassVar

from pydantic import BaseModel, Field

from .content_blocks import BaseContent, ReasoningContent
from .unified_message import UnifiedMessage


class UnifiedResponse(BaseModel):
    """Provider-agnostic response format."""

    STANDARD_STATUSES: ClassVar[list[str]] = ["completed", "in_progress", "failed"]

    id: str
    model: str
    messages: list[UnifiedMessage]

    usage: dict[str, int | float] = Field(default_factory=dict)
    cost: float | None = None

    provider: str
    provider_metadata: dict[str, Any] = Field(default_factory=dict)

    finish_reason: str | None = None
    status: str | None = None

    @property
    def text(self) -> str:
        """Quick access to text content from all messages."""
        if self.messages:
            return " ".join([msg.get_text() for msg in self.messages])
        return ""

    @property
    def reasoning(self) -> list[ReasoningContent]:
        """Quick access to reasoning blocks from all messages."""
        return [block for msg in self.messages for block in msg.get_reasoning()]

    def get_content_by_type(self, content_type: str) -> list[BaseContent]:
        """Get all content blocks of a specific type across all messages."""
        return [block for msg in self.messages for block in msg.get_content_by_type(content_type)]

    def is_standard_status(self) -> bool:
        """Check if this response uses a standard status value."""
        return self.status in self.STANDARD_STATUSES if self.status else False
