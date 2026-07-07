from __future__ import annotations

import pytest

pytest.importorskip("a2a")

from a2a.types import (  # noqa: E402
    Artifact,
    Message,
    Part,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
)

pytestmark = pytest.mark.a2a


def test_message_to_part_round_trips_text_metadata(a2a_modules) -> None:
    part = a2a_modules.utils.message_to_part(
        {
            "content": "hello from AG2",
            "role": "assistant",
            "trace_id": "trace-123",
            "flags": {"approved": True},
        }
    )

    assert part.WhichOneof("content") == "text"
    assert part.text == "hello from AG2"
    assert part.media_type == "text/plain"
    assert a2a_modules.utils.message_from_part(part) == {
        "content": "hello from AG2",
        "role": "assistant",
        "trace_id": "trace-123",
        "flags": {"approved": True},
    }


def test_message_to_part_round_trips_structured_data(a2a_modules) -> None:
    payload = {"content": {"kind": "data", "value": "structured"}}

    part = a2a_modules.utils.message_to_part(payload)

    assert part.WhichOneof("content") == "data"
    assert part.media_type == "application/json"
    assert a2a_modules.utils.message_from_part(part) == {"kind": "data", "value": "structured"}


def test_request_message_round_trips_context_and_client_tools(a2a_modules) -> None:
    request = a2a_modules.utils.RequestMessage(
        messages=[
            {"content": "first", "role": "user"},
            {"content": "second", "role": "assistant", "trace_id": "trace-456"},
        ],
        context={"session": "abc", "nested": {"approved": True}},
        client_tools=[{"type": "function", "function": {"name": "lookup"}}],
    )

    a2a_message = a2a_modules.utils.request_message_to_a2a(request, context_id="ctx-1")
    round_trip = a2a_modules.utils.request_message_from_a2a(a2a_message)

    assert a2a_message.role == Role.ROLE_USER
    assert a2a_message.context_id == "ctx-1"
    assert round_trip.messages == request.messages
    assert round_trip.context == {"session": "abc", "nested": {"approved": True}}
    assert round_trip.client_tools == [{"type": "function", "function": {"name": "lookup"}}]


def test_make_input_required_message_sets_agent_role_and_metadata(a2a_modules) -> None:
    message = a2a_modules.utils.make_input_required_message(
        text="Need confirmation",
        context_id="ctx-2",
        task_id="task-2",
        context={"step": "confirm"},
    )

    assert message.role == Role.ROLE_AGENT
    assert message.context_id == "ctx-2"
    assert message.task_id == "task-2"
    assert len(message.parts) == 1
    assert message.parts[0].text == "Need confirmation"
    assert a2a_modules.utils._struct_to_dict(message.metadata) == {
        a2a_modules.utils.CONTEXT_KEY: {"step": "confirm"}
    }


def test_response_message_from_input_required_task_uses_status_message(a2a_modules) -> None:
    prior_message = Message(
        role=Role.ROLE_AGENT,
        parts=[Part(text="Previous reply", media_type="text/plain")],
    )
    status_message = a2a_modules.utils.make_input_required_message(
        text="Please provide the missing field",
        context_id="ctx-3",
        task_id="task-3",
        context={"step": "collect-email"},
    )
    task = Task(
        id="task-3",
        context_id="ctx-3",
        history=[prior_message],
        status=TaskStatus(
            state=TaskState.TASK_STATE_INPUT_REQUIRED,
            message=status_message,
        ),
    )

    response = a2a_modules.utils.response_message_from_a2a_task(task)

    assert response is not None
    assert response.input_required == "Please provide the missing field"
    assert response.context == {"step": "collect-email"}
    assert response.messages[0] == {"content": "Previous reply"}
    assert response.messages[-1] == {
        "content": "Please provide the missing field",
        "role": "assistant",
    }


def test_copy_artifact_merges_context_metadata(a2a_modules) -> None:
    artifact = a2a_modules.utils.make_artifact(
        {"content": "first"},
        context={"request_id": "req-1"},
    )
    copied = a2a_modules.utils.copy_artifact(
        artifact,
        {"content": "second"},
        context={"step": "follow-up"},
    )

    assert copied.artifact_id == artifact.artifact_id
    assert copied.parts[0].text == "second"
    assert a2a_modules.utils._struct_to_dict(copied.metadata) == {
        a2a_modules.utils.CONTEXT_KEY: {"request_id": "req-1", "step": "follow-up"}
    }


def test_update_artifact_to_streaming_yields_chunks_until_last_chunk(a2a_modules) -> None:
    event = TaskArtifactUpdateEvent(
        task_id="task-4",
        context_id="ctx-4",
        artifact=Artifact(
            artifact_id="artifact-1",
            parts=[
                Part(text="hello", media_type="text/plain"),
                Part(data=a2a_modules.utils._value_from_python({"content": "world"}), media_type="application/json"),
            ],
        ),
        last_chunk=False,
    )

    chunks = [stream_event.content.content for stream_event in a2a_modules.utils.update_artifact_to_streaming(event)]

    assert chunks == ["hello", "world"]
