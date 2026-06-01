import asyncio

import pytest


def _build_falkor_engine():
    pytest.importorskip("falkordb")
    pytest.importorskip("graphrag_sdk")

    from autogen.agentchat.contrib.graph_rag.falkor_graph_query_engine import FalkorGraphQueryEngine

    return object.__new__(FalkorGraphQueryEngine)


def _build_neo4j_native_engine():
    pytest.importorskip("neo4j")
    pytest.importorskip("neo4j_graphrag")

    from autogen.agentchat.contrib.graph_rag.neo4j_native_graph_query_engine import Neo4jNativeGraphQueryEngine

    return object.__new__(Neo4jNativeGraphQueryEngine)


@pytest.fixture(params=[_build_falkor_engine, _build_neo4j_native_engine], ids=["falkor", "neo4j-native"])
def engine(request):
    return request.param()


async def _return_value(value: str) -> str:
    return value


async def _raise_value_error(message: str) -> None:
    raise ValueError(message)


def test_run_async_without_running_loop_returns_result(engine) -> None:
    assert engine._run_async(_return_value("expected-result")) == "expected-result"


def test_run_async_with_running_loop_returns_result(engine) -> None:
    async def driver() -> str:
        return engine._run_async(_return_value("expected-result"))

    assert asyncio.run(driver()) == "expected-result"


def test_run_async_without_running_loop_propagates_exceptions(engine) -> None:
    with pytest.raises(ValueError, match="expected-error"):
        engine._run_async(_raise_value_error("expected-error"))


def test_run_async_with_running_loop_propagates_exceptions(engine) -> None:
    async def driver() -> None:
        engine._run_async(_raise_value_error("expected-error"))

    with pytest.raises(ValueError, match="expected-error"):
        asyncio.run(driver())
