# Copyright (c) 2023 - 2026, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0
#
# Based on OpenTelemetry GenAI semantic conventions
# https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/

from enum import Enum

from autogen.version import __version__ as AG2_VERSION  # noqa: N812


class SpanType(str, Enum):
    CONVERSATION = "conversation"
    MULTI_CONVERSATION = "multi_conversation"
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    HANDOFF = "handoff"
    SPEAKER_SELECTION = "speaker_selection"
    HUMAN_INPUT = "human_input"
    CODE_EXECUTION = "code_execution"


OTEL_SCHEMA = "https://opentelemetry.io/schemas/1.11.0"
INSTRUMENTING_MODULE_NAME = "opentelemetry.instrumentation.ag2"
INSTRUMENTING_LIBRARY_VERSION = AG2_VERSION
