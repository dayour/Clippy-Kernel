# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

import inspect
import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes, create_rest_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from google.protobuf.json_format import ParseDict
from pydantic import BaseModel, ConfigDict, Field

from autogen import ConversableAgent
from autogen.doc_utils import export_module

from .agent_executor import AutogenAgentExecutor

if TYPE_CHECKING:
    from a2a.server.agent_execution import RequestContextBuilder
    from a2a.server.context import ServerCallContext
    from a2a.server.events import QueueManager
    from a2a.server.request_handlers import RequestHandler
    from a2a.server.routes import ServerCallContextBuilder
    from a2a.server.tasks import PushNotificationConfigStore, PushNotificationSender, TaskStore
    from starlette.applications import Starlette


def _copy_agent_card(card: AgentCard) -> AgentCard:
    copied = AgentCard()
    copied.CopyFrom(card)
    return copied


def _parse_proto(message_type: type, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, message_type):
        return value
    if isinstance(value, BaseModel):
        value = value.model_dump(exclude_none=True)
    return ParseDict(value, message_type(), ignore_unknown_fields=True)


@export_module("autogen.a2a")
class CardSettings(BaseModel):
    """Settings used to assemble an A2A 1.x AgentCard."""

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    name: str | None = None
    description: str | None = None
    url: str | None = None
    version: str = "0.1.0"
    default_input_modes: list[str] = Field(default_factory=lambda: ["text"])
    default_output_modes: list[str] = Field(default_factory=lambda: ["text"])
    capabilities: AgentCapabilities | dict[str, Any] | None = None
    skills: list[AgentSkill | dict[str, Any]] = Field(default_factory=list)
    provider: Any | None = None
    supported_interfaces: list[Any] | None = None
    documentation_url: str | None = None
    security_schemes: dict[str, Any] | None = None
    security_requirements: list[Any] | None = None
    signatures: list[Any] | None = None
    icon_url: str | None = None


@export_module("autogen.a2a")
class A2aAgentServer:
    """A server wrapper for running an AG2 agent via the A2A protocol."""

    def __init__(
        self,
        agent: "ConversableAgent",
        *,
        url: str | None = "http://localhost:8000",
        agent_card: CardSettings | None = None,
        card_modifier: Callable[["AgentCard"], "AgentCard"] | None = None,
        extended_agent_card: CardSettings | None = None,
        extended_card_modifier: Callable[["AgentCard", "ServerCallContext"], "AgentCard"] | None = None,
    ) -> None:
        self.agent = agent

        if not agent_card:
            agent_card = CardSettings()

        if agent_card.url and url != "http://localhost:8000":
            warnings.warn(
                (
                    "You can't use `agent_card.url` and `url` options in the same time. "
                    f"`agent_card.url` has a higher priority, so `{agent_card.url}` will be used."
                ),
                RuntimeWarning,
                stacklevel=2,
            )

        self.card = self._build_agent_card(
            settings=agent_card,
            fallback_url=url,
            extended_enabled=extended_agent_card is not None,
        )

        self.extended_agent_card: AgentCard | None = None
        if extended_agent_card:
            if extended_agent_card.url and url != "http://localhost:8000":
                warnings.warn(
                    (
                        "You can't use `extended_agent_card.url` and `url` options in the same time. "
                        f"`agent_card.url` has a higher priority, so `{extended_agent_card.url}` will be used."
                    ),
                    RuntimeWarning,
                    stacklevel=2,
                )

            self.extended_agent_card = self._build_agent_card(
                settings=extended_agent_card,
                fallback_url=url,
                extended_enabled=True,
            )

        self.card_modifier = card_modifier
        self.extended_card_modifier = extended_card_modifier
        self.middlewares: list[tuple[type[Any], dict[str, Any]]] = []

    def _default_supported_interfaces(self, url: str) -> list[AgentInterface]:
        return [
            AgentInterface(
                url=url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            ),
            AgentInterface(
                url=url,
                protocol_binding="HTTP+JSON",
                protocol_version="1.0",
            ),
        ]

    def _build_agent_card(
        self,
        *,
        settings: CardSettings,
        fallback_url: str | None,
        extended_enabled: bool,
    ) -> AgentCard:
        effective_url = settings.url or fallback_url or "http://localhost:8000"

        capabilities = _parse_proto(AgentCapabilities, settings.capabilities) or AgentCapabilities(streaming=True)
        capabilities.extended_agent_card = extended_enabled

        supported_interfaces = (
            [_parse_proto(AgentInterface, item) for item in settings.supported_interfaces]
            if settings.supported_interfaces
            else self._default_supported_interfaces(effective_url)
        )

        card = AgentCard(
            name=settings.name or self.agent.name,
            description=settings.description or self.agent.description,
            supported_interfaces=supported_interfaces,
            version=settings.version,
            capabilities=capabilities,
            default_input_modes=list(settings.default_input_modes),
            default_output_modes=list(settings.default_output_modes),
            skills=[_parse_proto(AgentSkill, item) for item in settings.skills],
        )

        if settings.provider is not None:
            card.provider.CopyFrom(_parse_proto(type(card.provider), settings.provider))
        if settings.documentation_url is not None:
            card.documentation_url = settings.documentation_url
        if settings.icon_url is not None:
            card.icon_url = settings.icon_url

        if settings.security_schemes:
            template = card.security_schemes.get_or_create("__template__")
            security_scheme_type = type(template)
            del card.security_schemes["__template__"]
            for key, value in settings.security_schemes.items():
                card.security_schemes[key].CopyFrom(_parse_proto(security_scheme_type, value))

        if settings.security_requirements:
            requirement_type = type(card.security_requirements.add())
            del card.security_requirements[:]
            card.security_requirements.extend(
                _parse_proto(requirement_type, item) for item in settings.security_requirements
            )

        if settings.signatures:
            signature_type = type(card.signatures.add())
            del card.signatures[:]
            card.signatures.extend(_parse_proto(signature_type, item) for item in settings.signatures)

        return card

    def add_middleware(self, middleware: type[Any], **kwargs: Any) -> None:
        """Add a middleware to the A2A server."""
        self.middlewares.append((middleware, kwargs))

    @property
    def executor(self) -> AutogenAgentExecutor:
        """Get the A2A agent executor."""
        return AutogenAgentExecutor(self.agent)

    def build_request_handler(
        self,
        *,
        task_store: "TaskStore | None" = None,
        queue_manager: "QueueManager | None" = None,
        push_config_store: "PushNotificationConfigStore | None" = None,
        push_sender: "PushNotificationSender | None" = None,
        request_context_builder: "RequestContextBuilder | None" = None,
    ) -> "RequestHandler":
        """Build a request handler for an A2A application."""
        return DefaultRequestHandler(
            agent_executor=self.executor,
            task_store=task_store or InMemoryTaskStore(),
            agent_card=self.card,
            queue_manager=queue_manager,
            push_config_store=push_config_store,
            push_sender=push_sender,
            request_context_builder=request_context_builder,
            extended_agent_card=self.extended_agent_card,
            extended_card_modifier=self._wrap_extended_card_modifier(),
        )

    def _wrap_extended_card_modifier(
        self,
    ) -> Callable[[AgentCard, "ServerCallContext"], Any] | None:
        if self.extended_card_modifier is None:
            return None

        async def modifier(card: AgentCard, context: "ServerCallContext") -> AgentCard:
            updated = self.extended_card_modifier(_copy_agent_card(card), context)
            if inspect.isawaitable(updated):
                updated = await updated
            return updated

        return modifier

    def _wrap_card_modifier(self) -> Callable[[AgentCard], Any] | None:
        if self.card_modifier is None:
            return None

        async def modifier(card: AgentCard) -> AgentCard:
            updated = self.card_modifier(_copy_agent_card(card))
            if inspect.isawaitable(updated):
                updated = await updated
            return updated

        return modifier

    def build_starlette_app(
        self,
        *,
        request_handler: "RequestHandler | None" = None,
        context_builder: "ServerCallContextBuilder | None" = None,
    ) -> "Starlette":
        """Build a Starlette A2A application for an ASGI server."""
        from starlette.applications import Starlette

        handler = request_handler or self.build_request_handler()
        app = Starlette()
        app.routes.extend(create_agent_card_routes(self.card, card_modifier=self._wrap_card_modifier()))
        app.routes.extend(create_jsonrpc_routes(handler, rpc_url="/", context_builder=context_builder))
        app.routes.extend(create_rest_routes(handler, context_builder=context_builder))

        for middleware, kwargs in self.middlewares:
            app.add_middleware(middleware, **kwargs)  # type: ignore[arg-type]

        return app

    build = build_starlette_app
