# Copyright (c) 2023 - 2025, clippy kernel development team
#
# SPDX-License-Identifier: Apache-2.0

"""Shared semantic metadata helpers for orchestration payloads."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_SEMANTIC_SCHEMA_VERSION = "1.0"


def _normalize_tag(value: str) -> str:
    normalized = value.strip().lower().replace("/", "-").replace("_", "-")
    return "-".join(normalized.split())


def _normalize_values(values: list[str] | None) -> list[str]:
    unique_values: list[str] = []
    for value in values or []:
        normalized = _normalize_tag(value)
        if normalized and normalized not in unique_values:
            unique_values.append(normalized)
    return unique_values


class SchemaDescriptor(BaseModel):
    """Schema descriptor for orchestration payloads."""

    name: str
    version: str = DEFAULT_SEMANTIC_SCHEMA_VERSION
    kind: str
    namespace: str = "clippy-kernel"


class RoutingHints(BaseModel):
    """Routing hints used by orchestration layers."""

    domain: str = "software-engineering"
    workflow: str
    primary_owner: str | None = None
    participant_roles: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class SemanticEnvelope(BaseModel):
    """Normalized semantic metadata attached to orchestration artifacts."""

    model_config = ConfigDict(populate_by_name=True)

    schema_descriptor: SchemaDescriptor = Field(alias="schema")
    semantic_tags: list[str] = Field(default_factory=list)
    routing_hints: RoutingHints
    attributes: dict[str, Any] = Field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a compact dictionary representation."""
        payload = self.model_dump(by_alias=True)
        if not payload["attributes"]:
            payload.pop("attributes")
        if not payload["routing_hints"].get("primary_owner"):
            payload["routing_hints"].pop("primary_owner")
        return payload


def build_semantic_envelope(
    *,
    schema_name: str,
    kind: str,
    workflow: str,
    tags: list[str] | None = None,
    primary_owner: str | None = None,
    participant_roles: list[str] | None = None,
    focus_areas: list[str] | None = None,
    capabilities: list[str] | None = None,
    attributes: dict[str, Any] | None = None,
    domain: str = "software-engineering",
) -> dict[str, Any]:
    """Create normalized semantic metadata for orchestration payloads."""
    normalized_tags = _normalize_values([domain, workflow, *(tags or [])])
    normalized_participants = _normalize_values(participant_roles)
    normalized_focus_areas = _normalize_values(focus_areas)
    normalized_capabilities = _normalize_values(capabilities)
    normalized_primary_owner = _normalize_tag(primary_owner) if primary_owner else None

    envelope = SemanticEnvelope(
        schema_descriptor=SchemaDescriptor(name=schema_name, kind=kind),
        semantic_tags=normalized_tags,
        routing_hints=RoutingHints(
            domain=_normalize_tag(domain),
            workflow=_normalize_tag(workflow),
            primary_owner=normalized_primary_owner,
            participant_roles=normalized_participants,
            focus_areas=normalized_focus_areas,
            capabilities=normalized_capabilities,
        ),
        attributes=attributes or {},
    )
    return envelope.as_dict()
