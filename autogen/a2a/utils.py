# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from a2a.types import Artifact, Message, Part, Role, Task, TaskArtifactUpdateEvent, TaskState
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Struct, Value

from autogen.agentchat.remote import RequestMessage, ResponseMessage
from autogen.events.client_events import StreamEvent

AG2_METADATA_KEY_PREFIX = "ag2_"
CLIENT_TOOLS_KEY = f"{AG2_METADATA_KEY_PREFIX}client_tools"
CONTEXT_KEY = f"{AG2_METADATA_KEY_PREFIX}context_update"

RESULT_ARTIFACT_NAME = "result"


def _struct_to_dict(struct: Struct | None) -> dict[str, Any]:
    if struct is None:
        return {}
    return MessageToDict(struct)


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
        ParseDict(data, value)
    return value


def _value_to_python(value: Value) -> Any:
    return MessageToDict(value)


def _part_to_text(part: Part) -> str:
    content_kind = part.WhichOneof("content")
    if content_kind == "text":
        return part.text
    if content_kind == "data":
        data = _value_to_python(part.data)
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return str(data.get("content", data))
        return str(data)
    if content_kind == "url":
        return part.url
    if content_kind == "raw":
        return part.raw.decode(errors="ignore")
    return ""


def _get_message_text(message: Message | None, delimiter: str = "\n") -> str:
    if message is None:
        return ""
    return delimiter.join(filter(None, (_part_to_text(part) for part in message.parts)))


def request_message_to_a2a(
    request_message: RequestMessage,
    context_id: str,
) -> Message:
    metadata: dict[str, Any] = {}
    if request_message.client_tools:
        metadata[CLIENT_TOOLS_KEY] = request_message.client_tools
    if request_message.context:
        metadata[CONTEXT_KEY] = request_message.context

    message = Message(
        role=Role.ROLE_USER,
        parts=[message_to_part(message) for message in request_message.messages],
        message_id=uuid4().hex,
        context_id=context_id,
    )
    if metadata:
        message.metadata.update(metadata)
    return message


def request_message_from_a2a(message: Message) -> RequestMessage:
    metadata = _struct_to_dict(message.metadata)
    return RequestMessage(
        messages=[message_from_part(part) for part in message.parts],
        context=metadata.get(CONTEXT_KEY),
        client_tools=metadata.get(CLIENT_TOOLS_KEY, []),
    )


def response_message_from_a2a_task(task: Task) -> ResponseMessage | None:
    history = [message_from_part(p) for m in task.history for p in m.parts]

    if task.status.state == TaskState.TASK_STATE_INPUT_REQUIRED:
        status_message = task.status.message if task.status.HasField("message") else None
        message = _get_message_text(status_message) if status_message else None
        context: dict[str, Any] | None = None

        if status_message:
            if status_message.metadata.fields:
                context = _struct_to_dict(status_message.metadata).get(CONTEXT_KEY)

            status_history = [message_from_part(part) for part in status_message.parts]
            for item in status_history:
                item.setdefault("role", "assistant")
            history.extend(status_history)
        elif task.history:
            message = _get_message_text(task.history[-1])
            if task.history[-1].metadata.fields:
                context = _struct_to_dict(task.history[-1].metadata).get(CONTEXT_KEY)
            if history:
                history[-1].setdefault("role", "assistant")

        return ResponseMessage(
            messages=history,
            input_required=message or "Please provide input:",
            context=context,
        )

    response = response_message_from_a2a_artifacts(list(task.artifacts))
    if response:
        response.messages = history + response.messages
    return response


def response_message_from_a2a_artifacts(artifacts: list[Artifact] | None) -> ResponseMessage | None:
    if not artifacts:
        return None

    if len(artifacts) > 1:
        raise NotImplementedError("Multiple artifacts are not supported")

    artifact = artifacts[-1]

    if not artifact.parts:
        return None

    metadata = _struct_to_dict(artifact.metadata) if artifact.metadata.fields else {}
    return ResponseMessage(
        messages=[message_from_part(p) for p in artifact.parts],
        context=metadata.get(CONTEXT_KEY),
    )


def update_artifact_to_streaming(event: TaskArtifactUpdateEvent) -> Iterator[StreamEvent]:
    if not event.last_chunk:
        for part in event.artifact.parts:
            yield StreamEvent(content=_part_to_text(part))


def response_message_from_a2a_message(message: Message) -> ResponseMessage | None:
    text_parts: list[Part] = []
    data_parts: list[Part] = []
    for part in message.parts:
        content_kind = part.WhichOneof("content")
        if content_kind == "text":
            text_parts.append(part)
        elif content_kind == "data":
            data_parts.append(part)
        else:
            raise NotImplementedError(f"Unsupported part type: {content_kind}")

    tpn = len(text_parts)
    if dpn := len(data_parts):
        if dpn > 1:
            raise NotImplementedError("Multiple data parts are not supported")

        if tpn:
            raise NotImplementedError("Data parts and text parts are not supported together")

        messages = [message_from_part(data_parts[0])]
    elif tpn == 1:
        messages = [message_from_part(text_parts[0])]
    else:
        messages = [{"content": "\n".join(part.text for part in text_parts)}]

    metadata = _struct_to_dict(message.metadata) if message.metadata.fields else {}
    return ResponseMessage(
        messages=messages,
        context=metadata.get(CONTEXT_KEY),
    )


def make_artifact(
    message: dict[str, Any] | None,
    context: dict[str, Any] | None = None,
    name: str = RESULT_ARTIFACT_NAME,
) -> Artifact:
    artifact = Artifact(
        artifact_id=uuid4().hex,
        name=name,
        parts=[message_to_part(message)] if message else [],
    )

    if context:
        artifact.metadata.update({CONTEXT_KEY: context})

    return artifact


def copy_artifact(
    artifact: Artifact,
    message: dict[str, Any] | None,
    context: dict[str, Any] | None = None,
) -> Artifact:
    updated_artifact = Artifact(
        artifact_id=artifact.artifact_id,
        description=artifact.description,
        parts=[message_to_part(message)] if message else [],
        name=artifact.name,
        extensions=list(artifact.extensions),
    )

    old_metadata = _struct_to_dict(artifact.metadata) if artifact.metadata.fields else {}
    merged_context = old_metadata.get(CONTEXT_KEY, {}) | (context or {})
    if merged_context:
        old_metadata[CONTEXT_KEY] = merged_context
    if old_metadata:
        updated_artifact.metadata.update(old_metadata)

    return updated_artifact


def make_input_required_message(
    text: str,
    context_id: str,
    task_id: str,
    context: dict[str, Any] | None = None,
) -> Message:
    message = Message(
        role=Role.ROLE_AGENT,
        context_id=context_id,
        task_id=task_id,
        message_id=uuid4().hex,
        parts=[Part(text=text, media_type="text/plain")],
    )
    if context:
        message.metadata.update({CONTEXT_KEY: context})
    return message


def message_to_part(message: dict[str, Any]) -> Part:
    message = message.copy()
    content = message.pop("content", "") or ""

    if isinstance(content, str):
        part = Part(
            text=content,
            media_type="text/plain",
        )
    else:
        part = Part(
            data=_value_from_python(content),
            media_type="application/json",
        )

    if message:
        part.metadata.update(message)

    return part


def message_from_part(part: Part) -> dict[str, Any]:
    metadata = _struct_to_dict(part.metadata) if part.metadata.fields else {}
    content_kind = part.WhichOneof("content")

    if content_kind == "text":
        return {
            **metadata,
            "content": part.text,
        }

    if content_kind == "data":
        data = _value_to_python(part.data)
        if (
            isinstance(data, dict)
            and set(data.keys()) == {RESULT_ARTIFACT_NAME}
            and metadata
            and "json_schema" in metadata
            and isinstance(result_data := data[RESULT_ARTIFACT_NAME], dict)
        ):
            return result_data

        if isinstance(data, dict):
            return data
        return {
            **metadata,
            "content": data,
        }

    raise NotImplementedError(f"Unsupported part type: {content_kind}")
