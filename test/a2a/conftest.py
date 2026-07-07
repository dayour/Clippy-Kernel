from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from pydantic import BaseModel, Field


def _install_remote_stub() -> None:
    if "autogen.agentchat.remote" in sys.modules:
        return

    remote_module = ModuleType("autogen.agentchat.remote")

    class AgentBusMessage(BaseModel):
        messages: list[dict] = Field(default_factory=list)
        context: dict | None = None

    class RequestMessage(AgentBusMessage):
        client_tools: list[dict] = Field(default_factory=list)

        @property
        def client_tool_names(self) -> set[str]:
            return {
                tool.get("function", {}).get("name", "")
                for tool in self.client_tools
                if tool.get("function", {}).get("name")
            }

    class ResponseMessage(AgentBusMessage):
        input_required: str | None = None

    class ServiceResponse(BaseModel):
        message: dict | None = None
        context: dict | None = None
        input_required: str | None = None
        streaming_text: str | None = None

    class RemoteAgentError(Exception):
        pass

    class RemoteAgentNotFoundError(RemoteAgentError):
        def __init__(self, agent_name: str) -> None:
            self.agent_name = agent_name
            super().__init__(f"Remote agent `{agent_name}` not found")

    class AgentService:
        def __init__(self, agent: object) -> None:
            self.agent = agent

    remote_module.AgentBusMessage = AgentBusMessage
    remote_module.RequestMessage = RequestMessage
    remote_module.ResponseMessage = ResponseMessage
    remote_module.ServiceResponse = ServiceResponse
    remote_module.RemoteAgentError = RemoteAgentError
    remote_module.RemoteAgentNotFoundError = RemoteAgentNotFoundError
    remote_module.AgentService = AgentService
    remote_module.__all__ = (
        "AgentBusMessage",
        "RequestMessage",
        "ResponseMessage",
        "ServiceResponse",
        "RemoteAgentError",
        "RemoteAgentNotFoundError",
        "AgentService",
    )
    sys.modules["autogen.agentchat.remote"] = remote_module


def _install_agent_executor_stub() -> None:
    module_name = "autogen.a2a.agent_executor"
    if module_name in sys.modules:
        return

    agent_executor_module = ModuleType(module_name)

    class AutogenAgentExecutor:
        def __init__(self, agent: object) -> None:
            self.agent = agent

    agent_executor_module.AutogenAgentExecutor = AutogenAgentExecutor
    sys.modules[module_name] = agent_executor_module


def _load_owned_a2a_module(repo_root: Path, module_name: str) -> ModuleType:
    package_name = "autogen.a2a"
    if package_name not in sys.modules:
        package = ModuleType(package_name)
        package.__path__ = [str(repo_root / "autogen" / "a2a")]  # type: ignore[attr-defined]
        sys.modules[package_name] = package

    qualified_name = f"{package_name}.{module_name}"
    if qualified_name in sys.modules:
        return sys.modules[qualified_name]

    module_path = repo_root / "autogen" / "a2a" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def a2a_modules() -> SimpleNamespace:
    pytest.importorskip("a2a")

    repo_root = Path(__file__).resolve().parents[2]
    _install_remote_stub()
    _install_agent_executor_stub()

    utils = _load_owned_a2a_module(repo_root, "utils")
    errors = _load_owned_a2a_module(repo_root, "errors")
    client_factory = _load_owned_a2a_module(repo_root, "client_factory")
    server = _load_owned_a2a_module(repo_root, "server")
    client = _load_owned_a2a_module(repo_root, "client")

    return SimpleNamespace(
        client=client,
        client_factory=client_factory,
        errors=errors,
        server=server,
        utils=utils,
    )
