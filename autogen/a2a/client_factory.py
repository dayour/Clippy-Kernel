# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

import ssl
import typing
from typing import Any, Protocol
from uuid import uuid4

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, Message, Part, Role, SendMessageResponse
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.protobuf.json_format import MessageToJson
from google.protobuf.struct_pb2 import Value
from httpx import MockTransport, Request, Response
from httpx._client import AsyncClient, Client, EventHook
from httpx._config import DEFAULT_LIMITS, DEFAULT_MAX_REDIRECTS, DEFAULT_TIMEOUT_CONFIG, Limits
from httpx._transports.base import AsyncBaseTransport
from httpx._types import AuthTypes, CertTypes, CookieTypes, HeaderTypes, ProxyTypes, QueryParamTypes, TimeoutTypes
from httpx._urls import URL

from autogen.doc_utils import export_module

EXTENDED_AGENT_CARD_PATH = "/extendedAgentCard"
PREV_AGENT_CARD_WELL_KNOWN_PATH = "/.well-known/agent.json"


def _value_from_python(data: Any) -> Value:
    value = Value()
    if data is None:
        value.null_value = 0
    elif isinstance(data, bool):
        value.bool_value = data
    elif isinstance(data, (int, float)):
        value.number_value = data
    elif isinstance(data, str):
        value.string_value = data
    else:
        from google.protobuf.json_format import ParseDict

        ParseDict(data, value)
    return value


def _response_message_to_part(response_message: str | dict[str, Any] | Part) -> Part:
    if isinstance(response_message, Part):
        return response_message
    if isinstance(response_message, str):
        return Part(text=response_message, media_type="text/plain")
    return Part(data=_value_from_python({"role": "assistant", **response_message}), media_type="application/json")


class ClientFactory(Protocol):
    def __call__(self) -> AsyncClient: ...

    def make_sync(self) -> Client: ...


@export_module("autogen.a2a")
class HttpxClientFactory(ClientFactory):
    """
    An asynchronous HTTP client factory, with connection pooling, HTTP/2, redirects,
    cookie persistence, etc.

    It can be shared between tasks.
    """

    def __init__(
        self,
        *,
        auth: AuthTypes | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        verify: ssl.SSLContext | str | bool = True,
        cert: CertTypes | None = None,
        http1: bool = True,
        http2: bool = False,
        proxy: ProxyTypes | None = None,
        mounts: None | (typing.Mapping[str, AsyncBaseTransport | None]) = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT_CONFIG,
        follow_redirects: bool = False,
        limits: Limits = DEFAULT_LIMITS,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        event_hooks: None | (typing.Mapping[str, list[EventHook]]) = None,
        base_url: URL | str = "",
        transport: AsyncBaseTransport | None = None,
        trust_env: bool = True,
        default_encoding: str | typing.Callable[[bytes], str] = "utf-8",
        **kwargs: typing.Any,
    ) -> None:
        self.options = {
            "auth": auth,
            "params": params,
            "headers": headers,
            "cookies": cookies,
            "verify": verify,
            "cert": cert,
            "http1": http1,
            "http2": http2,
            "proxy": proxy,
            "mounts": mounts,
            "timeout": timeout,
            "follow_redirects": follow_redirects,
            "limits": limits,
            "max_redirects": max_redirects,
            "event_hooks": event_hooks,
            "base_url": base_url,
            "transport": transport,
            "trust_env": trust_env,
            "default_encoding": default_encoding,
            **kwargs,
        }

    def __call__(self) -> AsyncClient:
        return AsyncClient(**self.options)

    def make_sync(self) -> Client:
        return Client(**self.options)


class EmptyClientFactory(ClientFactory):
    def __call__(self) -> AsyncClient:
        return AsyncClient(timeout=30.0)

    def make_sync(self) -> Client:
        return Client(timeout=30.0)


@export_module("autogen.a2a")
def MockClient(  # noqa: N802
    response_message: str | dict[str, Any] | Part,
) -> HttpxClientFactory:
    """Create a mock HTTP client for testing A2A agent interactions."""

    response_part = _response_message_to_part(response_message)

    async def mock_handler(request: Request) -> Response:
        if (
            request.url.path == AGENT_CARD_WELL_KNOWN_PATH
            or request.url.path == EXTENDED_AGENT_CARD_PATH
            or request.url.path == PREV_AGENT_CARD_WELL_KNOWN_PATH
        ):
            return Response(
                status_code=200,
                content=MessageToJson(
                    AgentCard(
                        capabilities=AgentCapabilities(streaming=False),
                        default_input_modes=["text"],
                        default_output_modes=["text"],
                        supported_interfaces=[
                            AgentInterface(
                                url="http://localhost:8000",
                                protocol_binding="JSONRPC",
                                protocol_version="1.0",
                            )
                        ],
                        name="mock_agent",
                        description="mock_agent",
                        version="0.1.0",
                        skills=[],
                    )
                ),
            )

        return Response(
            status_code=200,
            content=MessageToJson(
                SendMessageResponse(
                    message=Message(
                        message_id=str(uuid4()),
                        role=Role.ROLE_AGENT,
                        parts=[response_part],
                    )
                )
            ),
        )

    return HttpxClientFactory(transport=MockTransport(handler=mock_handler))
