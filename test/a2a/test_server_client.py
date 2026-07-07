from __future__ import annotations

import pytest

pytest.importorskip("a2a")

from a2a.types import (  # noqa: E402
    Artifact,
    Part,
    StreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

from autogen import ConversableAgent  # noqa: E402

pytestmark = pytest.mark.a2a


@pytest.fixture
def conversable_agent() -> ConversableAgent:
    return ConversableAgent(
        name="calendar-helper",
        description="Answers scheduling questions",
        llm_config=False,
    )


def test_agent_card_defaults_include_supported_interfaces(a2a_modules, conversable_agent: ConversableAgent) -> None:
    server = a2a_modules.server.A2aAgentServer(conversable_agent, url="https://agent.example.com")

    assert server.card.name == "calendar-helper"
    assert server.card.description == "Answers scheduling questions"
    assert [interface.protocol_binding for interface in server.card.supported_interfaces] == [
        "JSONRPC",
        "HTTP+JSON",
    ]
    assert [interface.url for interface in server.card.supported_interfaces] == [
        "https://agent.example.com",
        "https://agent.example.com",
    ]
    assert server.card.capabilities.streaming is True
    assert server.card.capabilities.extended_agent_card is False


def test_agent_card_sets_extended_capability_and_custom_interfaces(
    a2a_modules, conversable_agent: ConversableAgent
) -> None:
    server = a2a_modules.server.A2aAgentServer(
        conversable_agent,
        url="https://public.example.com",
        agent_card=a2a_modules.server.CardSettings(name="public-card"),
        extended_agent_card=a2a_modules.server.CardSettings(
            name="extended-card",
            capabilities={"streaming": False},
            supported_interfaces=[
                {
                    "url": "https://extended.example.com",
                    "protocol_binding": "HTTP+JSON",
                    "protocol_version": "1.0",
                }
            ],
        ),
    )

    assert server.card.capabilities.extended_agent_card is True
    assert server.extended_agent_card is not None
    assert server.extended_agent_card.name == "extended-card"
    assert server.extended_agent_card.capabilities.streaming is False
    assert server.extended_agent_card.capabilities.extended_agent_card is True
    assert len(server.extended_agent_card.supported_interfaces) == 1
    assert server.extended_agent_card.supported_interfaces[0].url == "https://extended.example.com"
    assert server.extended_agent_card.supported_interfaces[0].protocol_binding == "HTTP+JSON"


def test_apply_artifact_update_appends_parts_and_overwrites_metadata(a2a_modules) -> None:
    task = Task(
        id="task-1",
        context_id="ctx-1",
        status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
        artifacts=[
            Artifact(
                artifact_id="artifact-1",
                name="partial-result",
                description="before",
                parts=[Part(text="Hello", media_type="text/plain")],
            )
        ],
    )
    event = TaskArtifactUpdateEvent(
        task_id="task-1",
        context_id="ctx-1",
        append=True,
        artifact=Artifact(
            artifact_id="artifact-1",
            name="final-result",
            description="after",
            parts=[Part(text=" world", media_type="text/plain")],
            metadata={a2a_modules.utils.CONTEXT_KEY: {"step": "done"}},
        ),
    )

    a2a_modules.client._apply_artifact_update(task, event)

    assert [part.text for part in task.artifacts[0].parts] == ["Hello", " world"]
    assert task.artifacts[0].name == "final-result"
    assert task.artifacts[0].description == "after"
    assert a2a_modules.utils._struct_to_dict(task.artifacts[0].metadata) == {
        a2a_modules.utils.CONTEXT_KEY: {"step": "done"}
    }


def test_update_task_from_stream_response_tracks_status_and_artifacts(a2a_modules) -> None:
    working_response = StreamResponse(
        status_update=TaskStatusUpdateEvent(
            task_id="task-2",
            context_id="ctx-2",
            status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
        )
    )
    task, artifact_event = a2a_modules.client._update_task_from_stream_response(None, working_response)

    assert task is not None
    assert task.id == "task-2"
    assert task.context_id == "ctx-2"
    assert task.status.state == TaskState.TASK_STATE_WORKING
    assert artifact_event is None

    artifact_response = StreamResponse(
        artifact_update=TaskArtifactUpdateEvent(
            task_id="task-2",
            context_id="ctx-2",
            append=False,
            artifact=Artifact(
                artifact_id="artifact-2",
                parts=[Part(text="finished", media_type="text/plain")],
            ),
        )
    )
    task, artifact_event = a2a_modules.client._update_task_from_stream_response(task, artifact_response)

    assert artifact_event is not None
    assert len(task.artifacts) == 1
    assert task.artifacts[0].artifact_id == "artifact-2"
    assert task.artifacts[0].parts[0].text == "finished"

    completed_response = StreamResponse(
        status_update=TaskStatusUpdateEvent(
            task_id="task-2",
            context_id="ctx-2",
            status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
        )
    )
    task, _ = a2a_modules.client._update_task_from_stream_response(task, completed_response)

    assert task is not None
    assert task.status.state == TaskState.TASK_STATE_COMPLETED
    assert a2a_modules.client._is_task_completed(task) is True
    assert a2a_modules.client._is_stream_response_completed(completed_response, task) is True


def test_is_task_completed_raises_for_failed_tasks(a2a_modules) -> None:
    task = Task(
        id="task-3",
        context_id="ctx-3",
        status=TaskStatus(state=TaskState.TASK_STATE_FAILED),
    )

    with pytest.raises(a2a_modules.errors.A2aClientError, match="Task failed"):
        a2a_modules.client._is_task_completed(task)
