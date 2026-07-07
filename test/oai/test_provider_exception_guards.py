import importlib
import sys
import types
from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from autogen import OpenAIWrapper
from autogen.oai.oai_models import ChatCompletion, ChatCompletionMessage, Choice, CompletionUsage


class RaisingClient:
    def __init__(self, error: Exception):
        self.config = {"model_client_cls": "RaisingClient"}
        self.error = error
        self.call_count = 0

    def create(self, params: dict) -> ChatCompletion:
        self.call_count += 1
        raise self.error

    def message_retrieval(self, response: ChatCompletion) -> list[str]:
        return [choice.message.content or "" for choice in response.choices]

    def cost(self, response: ChatCompletion) -> float:
        return 0.0

    @staticmethod
    def get_usage(response: ChatCompletion) -> dict[str, float | int | str]:
        return {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "cost": 0.0,
            "model": response.model,
        }


class SuccessClient:
    def __init__(self, name: str):
        self.config = {"model_client_cls": "SuccessClient", "name": name}
        self.name = name
        self.call_count = 0

    def create(self, params: dict) -> ChatCompletion:
        self.call_count += 1
        return ChatCompletion(
            id=f"chatcmpl-{self.name}",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=0,
                    message=ChatCompletionMessage(content=f"Response from {self.name}", role="assistant"),
                )
            ],
            created=1677652288,
            model=params.get("model", "gpt-4o-mini"),
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        )

    def message_retrieval(self, response: ChatCompletion) -> list[str]:
        return [choice.message.content or "" for choice in response.choices]

    def cost(self, response: ChatCompletion) -> float:
        return 0.0

    @staticmethod
    def get_usage(response: ChatCompletion) -> dict[str, float | int | str]:
        return {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "cost": 0.0,
            "model": response.model,
        }


def _wrapper_with_clients(*clients: RaisingClient | SuccessClient) -> OpenAIWrapper:
    config_list = [
        {"model": f"model-{index}", "api_key": f"key-{index}", "model_client_cls": client.config["model_client_cls"]}
        for index, client in enumerate(clients)
    ]
    wrapper = OpenAIWrapper(config_list=config_list)
    wrapper._clients = list(clients)
    return wrapper


def _make_module(name: str, *, package: bool = False, **attrs: object) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__package__ = name if package else name.rpartition(".")[0]
    if package:
        module.__path__ = []  # type: ignore[attr-defined]
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def _reloaded_module(module_name: str, fake_modules: dict[str, types.ModuleType]) -> Iterator[types.ModuleType]:
    module = importlib.import_module(module_name)
    with patch.dict(sys.modules, fake_modules, clear=False):
        try:
            yield importlib.reload(module)
        finally:
            importlib.reload(module)


@pytest.mark.parametrize(
    ("exception_name", "exception_attr"),
    [
        ("AnthropicRateLimitError", "anthorpic_RateLimitError"),
        ("MistralSDKError", "mistral_SDKError"),
        ("TogetherException", "together_TogetherException"),
        ("CohereTooManyRequestsError", "cohere_TooManyRequestsError"),
    ],
)
def test_wrapper_retries_on_provider_exception_guard(exception_name: str, exception_attr: str) -> None:
    error_type = type(exception_name, (Exception,), {})
    wrapper = _wrapper_with_clients(RaisingClient(error_type("provider failed")), SuccessClient("backup"))

    with (
        patch(f"autogen.oai.client.{exception_attr}", error_type),
        patch("autogen.oai.client.RETRYABLE_PROVIDER_EXCEPTIONS", (error_type,)),
    ):
        response = wrapper.create(messages=[{"role": "user", "content": "hello"}])

    assert response.choices[0].message.content == "Response from backup"
    assert wrapper._clients[0].call_count == 1
    assert wrapper._clients[1].call_count == 1


@pytest.mark.parametrize(
    ("exception_name", "exception_attr"),
    [
        ("AnthropicRateLimitError", "anthorpic_RateLimitError"),
        ("MistralSDKError", "mistral_SDKError"),
        ("TogetherException", "together_TogetherException"),
        ("CohereTooManyRequestsError", "cohere_TooManyRequestsError"),
    ],
)
def test_wrapper_surfaces_provider_exception_on_last_client(exception_name: str, exception_attr: str) -> None:
    error_type = type(exception_name, (Exception,), {})
    wrapper = _wrapper_with_clients(RaisingClient(error_type("provider failed")))

    with (
        patch(f"autogen.oai.client.{exception_attr}", error_type),
        patch("autogen.oai.client.RETRYABLE_PROVIDER_EXCEPTIONS", (error_type,)),
        pytest.raises(error_type, match="provider failed"),
    ):
        wrapper.create(messages=[{"role": "user", "content": "hello"}])

    assert wrapper._clients[0].call_count == 1


def test_mistral_module_prefers_v2_imports() -> None:
    v2_mistral = object()
    assistant_message = type("AssistantMessage", (), {})
    fake_mistral = _make_module("mistralai", package=True)
    fake_mistral_client = _make_module("mistralai.client", package=True, Mistral=v2_mistral)
    fake_mistral_client_models = _make_module(
        "mistralai.client.models",
        AssistantMessage=assistant_message,
        Function=type("Function", (), {}),
        FunctionCall=type("FunctionCall", (), {}),
        SystemMessage=type("SystemMessage", (), {}),
        ToolCall=type("ToolCall", (), {}),
        ToolMessage=type("ToolMessage", (), {}),
        UserMessage=type("UserMessage", (), {}),
    )
    fake_mistral.client = fake_mistral_client
    fake_mistral_client.models = fake_mistral_client_models

    with _reloaded_module(
        "autogen.oai.mistral",
        {
            "mistralai": fake_mistral,
            "mistralai.client": fake_mistral_client,
            "mistralai.client.models": fake_mistral_client_models,
        },
    ) as mistral_module:
        assert mistral_module.Mistral is v2_mistral
        assert mistral_module.AssistantMessage is assistant_message


def test_mistral_module_falls_back_to_legacy_imports() -> None:
    legacy_mistral = object()
    assistant_message = type("AssistantMessage", (), {})
    fake_mistral = _make_module(
        "mistralai",
        Mistral=legacy_mistral,
        AssistantMessage=assistant_message,
        Function=type("Function", (), {}),
        FunctionCall=type("FunctionCall", (), {}),
        SystemMessage=type("SystemMessage", (), {}),
        ToolCall=type("ToolCall", (), {}),
        ToolMessage=type("ToolMessage", (), {}),
        UserMessage=type("UserMessage", (), {}),
    )

    with (
        patch.dict(sys.modules, {"mistralai.client": None, "mistralai.client.models": None}, clear=False),
        _reloaded_module("autogen.oai.mistral", {"mistralai": fake_mistral}) as mistral_module,
    ):
        assert mistral_module.Mistral is legacy_mistral
        assert mistral_module.AssistantMessage is assistant_message


def test_cohere_module_prefers_v2_imports() -> None:
    client_v2 = object()
    tool_result = type("ToolResult", (), {})
    fake_cohere = _make_module("cohere", package=True, ClientV2=client_v2)
    fake_cohere_types = _make_module("cohere.types", package=True)
    fake_cohere_tool_result = _make_module("cohere.types.tool_result", ToolResult=tool_result)
    fake_cohere.types = fake_cohere_types
    fake_cohere_types.tool_result = fake_cohere_tool_result

    with _reloaded_module(
        "autogen.oai.cohere",
        {
            "cohere": fake_cohere,
            "cohere.types": fake_cohere_types,
            "cohere.types.tool_result": fake_cohere_tool_result,
        },
    ) as cohere_module:
        assert cohere_module.CohereV2 is client_v2
        assert cohere_module.ToolResult is tool_result


def test_cohere_module_falls_back_to_legacy_imports() -> None:
    legacy_client = object()
    tool_result = type("ToolResult", (), {})
    fake_cohere = _make_module("cohere", package=True, Client=legacy_client)
    fake_cohere_types = _make_module("cohere.types", ToolResult=tool_result)
    fake_cohere.types = fake_cohere_types

    with patch.dict(sys.modules, {"cohere.types.tool_result": None}, clear=False), _reloaded_module(
        "autogen.oai.cohere",
        {
            "cohere": fake_cohere,
            "cohere.types": fake_cohere_types,
        },
    ) as cohere_module:
        assert cohere_module.CohereV2 is legacy_client
        assert cohere_module.ToolResult is tool_result


def test_anthropic_module_prefers_v2_imports() -> None:
    anthropic_client = object()
    anthropic_bedrock = object()
    anthropic_vertex = object()
    fake_anthropic = _make_module("anthropic", package=True, __version__="0.30.0", Anthropic=anthropic_client)
    fake_anthropic_types = _make_module(
        "anthropic.types",
        Message=type("Message", (), {}),
        TextBlock=type("TextBlock", (), {}),
        ToolUseBlock=type("ToolUseBlock", (), {}),
    )
    fake_anthropic_lib = _make_module("anthropic.lib", package=True)
    fake_anthropic_bedrock = _make_module("anthropic.lib.bedrock", AnthropicBedrock=anthropic_bedrock)
    fake_anthropic_vertex = _make_module("anthropic.lib.vertex", AnthropicVertex=anthropic_vertex)
    fake_anthropic.types = fake_anthropic_types
    fake_anthropic.lib = fake_anthropic_lib

    with _reloaded_module(
        "autogen.oai.anthropic",
        {
            "anthropic": fake_anthropic,
            "anthropic.types": fake_anthropic_types,
            "anthropic.lib": fake_anthropic_lib,
            "anthropic.lib.bedrock": fake_anthropic_bedrock,
            "anthropic.lib.vertex": fake_anthropic_vertex,
        },
    ) as anthropic_module:
        assert anthropic_module.Anthropic is anthropic_client
        assert anthropic_module.AnthropicBedrock is anthropic_bedrock
        assert anthropic_module.AnthropicVertex is anthropic_vertex
        assert anthropic_module.TOOL_ENABLED is True


def test_anthropic_module_falls_back_to_legacy_imports() -> None:
    anthropic_client = object()
    anthropic_bedrock = object()
    anthropic_vertex = object()
    fake_anthropic = _make_module(
        "anthropic",
        package=True,
        __version__="0.23.1",
        Anthropic=anthropic_client,
        AnthropicBedrock=anthropic_bedrock,
        AnthropicVertex=anthropic_vertex,
    )
    fake_anthropic_types = _make_module(
        "anthropic.types",
        Message=type("Message", (), {}),
        TextBlock=type("TextBlock", (), {}),
        ToolUseBlock=type("ToolUseBlock", (), {}),
    )
    fake_anthropic.types = fake_anthropic_types

    with _reloaded_module(
        "autogen.oai.anthropic",
        {
            "anthropic": fake_anthropic,
            "anthropic.types": fake_anthropic_types,
        },
    ) as anthropic_module:
        assert anthropic_module.Anthropic is anthropic_client
        assert anthropic_module.AnthropicBedrock is anthropic_bedrock
        assert anthropic_module.AnthropicVertex is anthropic_vertex
        assert anthropic_module.TOOL_ENABLED is True


def test_client_module_prefers_top_level_together_exception_import() -> None:
    top_level_exception = type("TogetherException", (Exception,), {})
    fake_together = _make_module("together", package=True, Together=type("Together", (), {}), TogetherException=top_level_exception)

    with _reloaded_module("autogen.oai.client", {"together": fake_together}) as client_module:
        assert client_module.together_TogetherException is top_level_exception


def test_client_module_falls_back_to_legacy_together_exception_import() -> None:
    legacy_exception = type("TogetherException", (Exception,), {})
    fake_together = _make_module("together", package=True, Together=type("Together", (), {}))
    fake_together_error = _make_module("together.error", TogetherException=legacy_exception)
    fake_together.error = fake_together_error

    with _reloaded_module(
        "autogen.oai.client",
        {
            "together": fake_together,
            "together.error": fake_together_error,
        },
    ) as client_module:
        assert client_module.together_TogetherException is legacy_exception


def test_cohere_create_maps_v2_tool_calls_and_billed_usage() -> None:
    pytest.importorskip("cohere")
    from autogen.oai.cohere import CohereClient

    response = MagicMock()
    response.id = "cohere-response"
    response.message = MagicMock(
        tool_plan="Use weather lookup",
        tool_calls=[
            types.SimpleNamespace(
                id="tool-1",
                function=types.SimpleNamespace(name="lookup_weather", arguments=None),
            )
        ],
    )
    response.usage = MagicMock(billed_units=MagicMock(input_tokens=11, output_tokens=7))

    sdk_client = MagicMock()
    sdk_client.chat.return_value = response

    with patch("autogen.oai.cohere.CohereV2", return_value=sdk_client):
        client = CohereClient(api_key="dummy_api_key")
        result = client.create(
            {
                "model": "command-r-plus",
                "messages": [{"role": "user", "content": "What is the weather?"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "lookup_weather",
                            "description": "Look up weather.",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
            }
        )

    assert result.choices[0].finish_reason == "tool_calls"
    assert result.choices[0].message.content == "Use weather lookup"
    assert result.choices[0].message.tool_calls[0].function.name == "lookup_weather"
    assert result.choices[0].message.tool_calls[0].function.arguments == ""
    assert result.usage.prompt_tokens == 11
    assert result.usage.completion_tokens == 7
    assert result.usage.total_tokens == 18


def test_anthropic_create_maps_tool_use_blocks_and_usage() -> None:
    pytest.importorskip("anthropic")
    from anthropic.types import TextBlock, ToolUseBlock

    from autogen.oai.anthropic import AnthropicClient

    response = MagicMock()
    response.id = "msg_123"
    response.stop_reason = "tool_use"
    response.content = [
        ToolUseBlock(id="tool-1", name="lookup_weather", input={"city": "Seattle"}, type="tool_use"),
        TextBlock(text="Checking weather", type="text"),
    ]
    response.usage = MagicMock(input_tokens=9, output_tokens=4)

    sdk_client = MagicMock()
    sdk_client.messages.create.return_value = response

    with patch("autogen.oai.anthropic.Anthropic", return_value=sdk_client):
        client = AnthropicClient(api_key="dummy_api_key")
        result = client.create(
            {
                "model": "claude-3-5-sonnet-20240620",
                "messages": [{"role": "user", "content": "What is the weather?"}],
            }
        )

    assert result.choices[0].finish_reason == "tool_calls"
    assert result.choices[0].message.content == "Checking weather"
    assert result.choices[0].message.tool_calls[0].function.name == "lookup_weather"
    assert result.choices[0].message.tool_calls[0].function.arguments == '{"city": "Seattle"}'
    assert result.usage.prompt_tokens == 9
    assert result.usage.completion_tokens == 4
    assert result.usage.total_tokens == 13
