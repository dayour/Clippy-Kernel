# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from pprint import pformat
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, AgentCardResolutionError, Client, ClientCallInterceptor, ClientConfig
from a2a.client import ClientFactory as A2AClientFactory
from a2a.client.errors import A2AClientError as SDKA2AClientError
from a2a.types import (
    AgentCard,
    GetTaskRequest,
    SendMessageConfiguration,
    SendMessageRequest,
    StreamResponse,
    SubscribeToTaskRequest,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.protobuf.json_format import MessageToDict
from typing_extensions import Self

from autogen import ConversableAgent
from autogen.agentchat.remote import RequestMessage, ResponseMessage
from autogen.doc_utils import export_module
from autogen.events.agent_events import TerminationEvent
from autogen.io.base import IOStream
from autogen.oai.client import OpenAIWrapper

from .client_factory import ClientFactory, EmptyClientFactory
from .errors import A2aAgentNotFoundError, A2aClientError
from .utils import (
    request_message_to_a2a,
    response_message_from_a2a_message,
    response_message_from_a2a_task,
    update_artifact_to_streaming,
)

logger = logging.getLogger(__name__)

EXTENDED_AGENT_CARD_PATH = "/extendedAgentCard"
PREV_AGENT_CARD_WELL_KNOWN_PATH = "/.well-known/agent.json"


def _agent_endpoint(card: AgentCard | None, fallback: str) -> str:
    if card and card.supported_interfaces:
        return card.supported_interfaces[0].url
    return fallback


def _supports_streaming(card: AgentCard) -> bool:
    return bool(card.capabilities.streaming)


def _supports_extended_card(card: AgentCard) -> bool:
    return bool(card.capabilities.extended_agent_card)


def _copy_task(task: Task) -> Task:
    copied = Task()
    copied.CopyFrom(task)
    return copied


def _ensure_task(task: Task | None, response: StreamResponse) -> Task | None:
    if response.HasField("task"):
        return _copy_task(response.task)
    if task is None and response.HasField("status_update"):
        return Task(
            id=response.status_update.task_id,
            context_id=response.status_update.context_id,
            status=TaskStatus(state=response.status_update.status.state),
        )
    if task is None and response.HasField("artifact_update"):
        return Task(
            id=response.artifact_update.task_id,
            context_id=response.artifact_update.context_id,
            status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
        )
    return task


def _apply_artifact_update(task: Task, event: TaskArtifactUpdateEvent) -> None:
    for index, artifact in enumerate(task.artifacts):
        if artifact.artifact_id == event.artifact.artifact_id:
            if event.append:
                artifact.parts.extend(event.artifact.parts)
                if event.artifact.metadata.fields:
                    artifact.metadata.CopyFrom(event.artifact.metadata)
                if event.artifact.extensions:
                    del artifact.extensions[:]
                    artifact.extensions.extend(event.artifact.extensions)
                if event.artifact.name:
                    artifact.name = event.artifact.name
                if event.artifact.description:
                    artifact.description = event.artifact.description
            else:
                task.artifacts[index].CopyFrom(event.artifact)
            return
    task.artifacts.append(event.artifact)


def _update_task_from_stream_response(
    task: Task | None,
    response: StreamResponse,
) -> tuple[Task | None, TaskArtifactUpdateEvent | None]:
    task = _ensure_task(task, response)

    if task is None:
        return None, None

    if response.HasField("task"):
        return task, None

    if response.HasField("status_update"):
        task.status.CopyFrom(response.status_update.status)
        return task, None

    if response.HasField("artifact_update"):
        _apply_artifact_update(task, response.artifact_update)
        return task, response.artifact_update

    return task, None


@export_module("autogen.a2a")
class A2aRemoteAgent(ConversableAgent):
    """`a2a-sdk`-based client for handling asynchronous communication with an A2A server."""

    def __init__(
        self,
        url: str,
        name: str,
        *,
        silent: bool | None = None,
        client: ClientFactory | None = None,
        client_config: ClientConfig | None = None,
        interceptors: Sequence[ClientCallInterceptor] = (),
        max_reconnects: int = 3,
        polling_interval: float = 0.5,
    ) -> None:
        self.url = url

        self._httpx_client_factory = client or EmptyClientFactory()
        self._card_resolver = A2ACardResolver(
            httpx_client=self._httpx_client_factory(),
            base_url=url,
        )

        self._max_reconnects = max_reconnects
        self._polling_interval = polling_interval

        super().__init__(name, silent=silent)

        self.__llm_config: dict[str, Any] = {}

        self._client_config = client_config or ClientConfig()
        self._interceptors = list(interceptors)
        self._agent_card: AgentCard | None = None

        self.replace_reply_func(
            ConversableAgent.generate_oai_reply,
            A2aRemoteAgent.generate_remote_reply,
        )
        self.replace_reply_func(
            ConversableAgent.a_generate_oai_reply,
            A2aRemoteAgent.a_generate_remote_reply,
        )

    @classmethod
    def from_card(
        cls,
        card: AgentCard,
        *,
        silent: bool | None = None,
        client: ClientFactory | None = None,
        client_config: ClientConfig | None = None,
        max_reconnects: int = 3,
        polling_interval: float = 0.5,
        interceptors: Sequence[ClientCallInterceptor] = (),
    ) -> Self:
        instance = cls(
            url=_agent_endpoint(card, "UNKNOWN"),
            name=card.name,
            silent=silent,
            client=client,
            client_config=client_config,
            max_reconnects=max_reconnects,
            polling_interval=polling_interval,
            interceptors=interceptors,
        )
        instance._agent_card = card
        return instance

    def generate_remote_reply(
        self,
        messages: list[dict[str, Any]] | None = None,
        sender: ConversableAgent | None = None,
        config: OpenAIWrapper | None = None,
    ) -> tuple[bool, dict[str, Any] | None]:
        raise NotImplementedError(f"{self.__class__.__name__} does not support synchronous reply generation")

    async def a_generate_remote_reply(
        self,
        messages: list[dict[str, Any]] | None = None,
        sender: ConversableAgent | None = None,
        config: OpenAIWrapper | None = None,
    ) -> tuple[bool, dict[str, Any] | None]:
        if messages is None:
            messages = self._oai_messages[sender]

        if not self._agent_card:
            self._agent_card = await self._get_agent_card()

        context_id = uuid4().hex

        self._client_config.httpx_client = self._httpx_client_factory()
        async with self._client_config.httpx_client:
            agent_client = A2AClientFactory(self._client_config).create(
                self._agent_card,
                interceptors=self._interceptors,
            )

            while True:
                initial_message = request_message_to_a2a(
                    request_message=RequestMessage(
                        messages=messages,
                        context=self.context_variables.data,
                        client_tools=self.__llm_config.get("tools", []),
                    ),
                    context_id=context_id,
                )
                request = SendMessageRequest(
                    message=initial_message,
                    configuration=SendMessageConfiguration(),
                )

                if _supports_streaming(self._agent_card):
                    a2a_stream = self._ask_streaming(agent_client, request)
                else:
                    a2a_stream = self._ask_polling(agent_client, request)

                io_stream = IOStream.get_default()

                reply: ResponseMessage | None = None
                current_task: Task | None = None
                async for a2a_event in a2a_stream:
                    if a2a_event.HasField("message"):
                        reply = response_message_from_a2a_message(a2a_event.message)
                        continue

                    current_task, artifact_event = _update_task_from_stream_response(current_task, a2a_event)
                    if artifact_event is not None:
                        for e in update_artifact_to_streaming(artifact_event):
                            io_stream.send(e)

                    if current_task and _is_task_completed(current_task):
                        reply = response_message_from_a2a_task(current_task)

                if not reply:
                    return True, None

                messages = reply.messages
                if reply.input_required is not None:
                    user_input = await self.a_get_human_input(prompt=f"Input for `{self.name}`\n{reply.input_required}")

                    if user_input == "exit":
                        io_stream.send(
                            TerminationEvent(
                                termination_reason="User requested to end the conversation",
                                sender=self,
                                recipient=sender,
                            )
                        )
                        return True, None

                    messages.append({"content": user_input, "role": "user"})
                    continue

                if sender and reply.context:
                    self.context_variables.update(reply.context)
                    sender.context_variables.update(reply.context)

                return True, reply.messages[-1]

    async def _ask_streaming(self, client: Client, request: SendMessageRequest) -> AsyncIterator[StreamResponse]:
        started_task: Task | None = None
        completed = False
        try:
            async for event in client.send_message(request):
                if event.HasField("task"):
                    started_task = _copy_task(event.task)
                yield event
                completed = _is_stream_response_completed(event, started_task)

        except (httpx.ConnectError, SDKA2AClientError) as e:
            if not started_task:
                if not self._agent_card:
                    raise A2aClientError(f"Failed to connect to the agent: agent card not found. {e}") from e
                raise A2aClientError(
                    f"Failed to connect to the agent {self._agent_card.name!r} at {_agent_endpoint(self._agent_card, self.url)}: {e}"
                ) from e

        if not completed:
            if not started_task:
                if not self._agent_card:
                    raise A2aClientError("Failed to connect to the agent: agent card not found")
                raise A2aClientError(
                    f"Failed to connect to the agent {self._agent_card.name!r} at {_agent_endpoint(self._agent_card, self.url)}"
                )

            connection_attempts = 1
            while not completed and connection_attempts < self._max_reconnects:
                try:
                    async for event in client.subscribe(SubscribeToTaskRequest(id=started_task.id)):
                        yield event
                        completed = _is_stream_response_completed(event, started_task)

                except (httpx.ConnectError, SDKA2AClientError) as e:
                    connection_attempts += 1
                    if connection_attempts >= self._max_reconnects:
                        if not self._agent_card:
                            raise A2aClientError(f"Failed to connect to the agent: agent card not found. {e}") from e
                        raise A2aClientError(
                            f"Failed to connect to the agent {self._agent_card.name!r} at {_agent_endpoint(self._agent_card, self.url)}: {e}"
                        ) from e

    async def _ask_polling(self, client: Client, request: SendMessageRequest) -> AsyncIterator[StreamResponse]:
        started_task: Task | None = None
        completed = False
        try:
            async for event in client.send_message(request):
                if event.HasField("task"):
                    started_task = _copy_task(event.task)
                yield event
                completed = _is_stream_response_completed(event, started_task)

        except (httpx.ConnectError, SDKA2AClientError) as e:
            if not started_task:
                if not self._agent_card:
                    raise A2aClientError(f"Failed to connect to the agent: agent card not found. {e}") from e
                raise A2aClientError(
                    f"Failed to connect to the agent {self._agent_card.name!r} at {_agent_endpoint(self._agent_card, self.url)}: {e}"
                ) from e

        if not completed:
            if not started_task:
                if not self._agent_card:
                    raise A2aClientError("Failed to connect to the agent: agent card not found")
                raise A2aClientError(
                    f"Failed to connect to the agent {self._agent_card.name!r} at {_agent_endpoint(self._agent_card, self.url)}"
                )

            connection_attempts = 1
            while not completed and connection_attempts < self._max_reconnects:
                try:
                    task = await client.get_task(GetTaskRequest(id=started_task.id))
                    started_task = _copy_task(task)
                    yield StreamResponse(task=task)
                    completed = _is_task_completed(task)

                except (httpx.ConnectError, SDKA2AClientError) as e:
                    connection_attempts += 1
                    if connection_attempts >= self._max_reconnects:
                        if not self._agent_card:
                            raise A2aClientError(f"Failed to connect to the agent: agent card not found. {e}") from e
                        raise A2aClientError(
                            f"Failed to connect to the agent {self._agent_card.name!r} at {_agent_endpoint(self._agent_card, self.url)}: {e}"
                        ) from e

                else:
                    await asyncio.sleep(self._polling_interval)

    def update_tool_signature(
        self,
        tool_sig: str | dict[str, Any],
        is_remove: bool,
        silent_override: bool = False,
    ) -> None:
        self.__llm_config = self._update_tool_config(
            self.__llm_config,
            tool_sig=tool_sig,
            is_remove=is_remove,
            silent_override=silent_override,
        )

    async def _get_agent_card(
        self,
        auth_http_kwargs: dict[str, Any] | None = None,
    ) -> AgentCard:
        card: AgentCard | None = None

        try:
            logger.info(
                f"Attempting to fetch public agent card from: {self._card_resolver.base_url}{AGENT_CARD_WELL_KNOWN_PATH}"
            )

            try:
                card = await self._card_resolver.get_agent_card(relative_card_path=AGENT_CARD_WELL_KNOWN_PATH)
            except AgentCardResolutionError as e_public:
                if e_public.status_code == 404:
                    logger.info(
                        f"Attempting to fetch public agent card from: {self._card_resolver.base_url}{PREV_AGENT_CARD_WELL_KNOWN_PATH}"
                    )
                    card = await self._card_resolver.get_agent_card(relative_card_path=PREV_AGENT_CARD_WELL_KNOWN_PATH)
                else:
                    raise

            if card and _supports_extended_card(card):
                try:
                    card = await self._card_resolver.get_agent_card(
                        relative_card_path=EXTENDED_AGENT_CARD_PATH,
                        http_kwargs=auth_http_kwargs,
                    )
                except Exception as e_extended:
                    logger.warning(
                        f"Failed to fetch extended agent card: {e_extended}. Will proceed with public card.",
                        exc_info=True,
                    )

        except Exception as e:
            raise A2aAgentNotFoundError(f"{self.name}: {self._card_resolver.base_url}") from e

        return card


def _task_to_pretty_dict(task: Task) -> dict[str, Any]:
    return MessageToDict(task, preserving_proto_field_name=True)


def _is_stream_response_completed(event: StreamResponse, current_task: Task | None) -> bool:
    if event.HasField("message"):
        return True
    if event.HasField("task"):
        return _is_task_completed(event.task)
    if current_task is None:
        return False
    if event.HasField("status_update"):
        current_task.status.CopyFrom(event.status_update.status)
    return _is_task_completed(current_task)


def _is_task_completed(task: Task) -> bool:
    if task.status.state == TaskState.TASK_STATE_FAILED:
        raise A2aClientError(f"Task failed: {pformat(_task_to_pretty_dict(task))}")

    if task.status.state == TaskState.TASK_STATE_REJECTED:
        raise A2aClientError(f"Task rejected: {pformat(_task_to_pretty_dict(task))}")

    return task.status.state in (
        TaskState.TASK_STATE_COMPLETED,
        TaskState.TASK_STATE_CANCELED,
        TaskState.TASK_STATE_INPUT_REQUIRED,
    )
