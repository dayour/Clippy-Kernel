# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import warnings
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from ....import_utils import optional_import_block, require_optional_import
from .document import Document
from .graph_query_engine import GraphStoreQueryResult

with optional_import_block():
    from falkordb import FalkorDB, Graph
    from graphrag_sdk import ConnectionConfig, GraphRAG, LiteLLM, LiteLLMEmbedder, Ontology
    from graphrag_sdk.core.providers import Embedder, LLMInterface


@require_optional_import(["falkordb", "graphrag_sdk"], "graph-rag-falkor-db")
class FalkorGraphQueryEngine:
    """Wrapper for FalkorDB GraphRAG SDK 1.x.

    The upstream SDK is async-first in 1.x, while the AG2 graph query engine
    contract is still synchronous. This class keeps the public sync methods and
    bridges them to the async GraphRAG facade internally.
    """

    def __init__(  # type: ignore[no-any-unimported]
        self,
        name: str,
        host: str = "127.0.0.1",
        port: int = 6379,
        username: str | None = None,
        password: str | None = None,
        model: Any | None = None,
        ontology: Optional["Ontology"] = None,
        llm: Optional["LLMInterface"] = None,
        embedder: Optional["Embedder"] = None,
        embedding_dimension: int = 256,
    ):
        """Initialize a FalkorDB knowledge graph.

        Please also refer to https://github.com/FalkorDB/GraphRAG-SDK.

        TODO: Fix LLM API cost calculation for FalkorDB usages.

        Args:
            name (str): Knowledge graph name.
            host (str): FalkorDB hostname.
            port (int): FalkorDB port number.
            username (str|None): FalkorDB username.
            password (str|None): FalkorDB password.
            model: Back-compat alias for the LLM provider. Accepts either a
                GraphRAG SDK provider instance or a model name string that will
                be wrapped with LiteLLM.
            ontology: FalkorDB knowledge graph ontology. If None, GraphRAG SDK
                will infer the ontology during the first ingest.
            llm: Explicit GraphRAG SDK LLM provider. Preferred over ``model``.
            embedder: Explicit GraphRAG SDK embedding provider.
            embedding_dimension: Expected embedding dimension for the graph
                vector store. Defaults to 256, matching the SDK quickstart.
        """
        self.name = name
        self.ontology_table_name = f"{name}__ontology"
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.llm = self._coerce_llm(llm=llm, model=model)
        self.embedder = embedder or LiteLLMEmbedder(
            model="openai/text-embedding-3-small", dimensions=embedding_dimension
        )
        self.embedding_dimension = embedding_dimension
        self.ontology = ontology
        self._chat_history: list[dict[str, str]] = []
        self.falkordb = FalkorDB(host=self.host, port=self.port, username=self.username, password=self.password)

    def connect_db(self) -> None:
        """Connect to an existing knowledge graph."""
        if self.name in self.falkordb.list_graphs():
            try:
                self.ontology = self._load_ontology_from_db()
            except Exception:
                warnings.warn("Graph Ontology is not loaded.")
            self._chat_history = []
        else:
            raise ValueError(f"Knowledge graph '{self.name}' does not exist")

    def init_db(self, input_doc: list[Document]) -> None:
        """Build the knowledge graph with input documents."""
        if not input_doc:
            raise ValueError("No input documents could be loaded.")

        async def _init_db() -> None:
            async with self._create_rag() as rag:
                for index, doc in enumerate(input_doc):
                    if doc.path_or_url:
                        await rag.ingest(doc.path_or_url)
                    elif isinstance(doc.data, str):
                        await rag.ingest(source=self._build_document_id(doc, index), text=doc.data)
                    else:
                        raise ValueError("Each input document must provide either `path_or_url` or string `data`.")
                await rag.finalize()
                self.ontology = await rag.get_ontology()

        self._run_async(_init_db())
        self._chat_history = []

    def add_records(self, new_records: list[Document]) -> bool:
        raise NotImplementedError("This method is not supported by FalkorDB SDK yet.")

    def query(self, question: str, n_results: int = 1, **kwargs: Any) -> GraphStoreQueryResult:
        """Query the knowledge graph with a question and optional message history.

        Args:
        question: a human input question.
        n_results: number of returned results.
        kwargs:
            messages: a list of message history.

        Returns: FalkorGraphQueryResult
        """
        if self.name not in self.falkordb.list_graphs():
            raise ValueError("Knowledge graph has not been selected or created.")

        messages = kwargs.get("messages")
        system_message = kwargs.get("system_message", "")
        history = (
            self._build_completion_history(messages, system_message)
            if messages is not None
            else list(self._chat_history)
        )

        async def _query() -> GraphStoreQueryResult:
            async with self._create_rag() as rag:
                response = await rag.completion(question, history=history or None)
                return GraphStoreQueryResult(answer=response.answer, results=[])

        result = self._run_async(_query())
        if messages is None:
            self._chat_history.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": result.answer or ""},
            ])
        return result

    def delete(self) -> bool:
        """Delete graph and its data from database."""
        all_graphs = self.falkordb.list_graphs()
        if self.name in all_graphs:
            self.falkordb.select_graph(self.name).delete()
        if self.ontology_table_name in all_graphs:
            self.falkordb.select_graph(self.ontology_table_name).delete()
        return True

    def __get_ontology_storage_graph(self) -> "Graph":  # type: ignore[no-any-unimported]
        return self.falkordb.select_graph(self.ontology_table_name)

    def _save_ontology_to_db(self, ontology: "Ontology") -> None:  # type: ignore[no-any-unimported]
        """Persist ontology through the GraphRAG facade on first ingest/query."""
        self.ontology = ontology

    def _load_ontology_from_db(self) -> "Ontology":  # type: ignore[no-any-unimported]
        if self.ontology_table_name not in self.falkordb.list_graphs():
            raise ValueError(f"Knowledge graph {self.name} has not been created.")

        async def _get_ontology() -> "Ontology":
            async with self._create_rag() as rag:
                return await rag.get_ontology()

        return self._run_async(_get_ontology())

    def _create_rag(self) -> "GraphRAG":  # type: ignore[no-any-unimported]
        return GraphRAG(
            connection=ConnectionConfig(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                graph_name=self.name,
            ),
            llm=self.llm,
            embedder=self.embedder,
            ontology=self.ontology,
            embedding_dimension=self.embedding_dimension,
        )

    def _coerce_llm(self, llm: Optional["LLMInterface"], model: Any | None) -> "LLMInterface":  # type: ignore[no-any-unimported]
        if llm is not None:
            return llm
        if model is None:
            return LiteLLM(model="openai/gpt-4o")
        if isinstance(model, str):
            return LiteLLM(model=model)
        if hasattr(model, "ainvoke") and hasattr(model, "invoke"):
            return model
        raise TypeError(
            "`model` must be a GraphRAG SDK LLM provider or model name string. "
            "Pass `llm=` for an explicit provider instance."
        )

    def _build_document_id(self, doc: Document, index: int) -> str:
        if doc.path_or_url:
            return doc.path_or_url
        return f"{self.name}-document-{index}"

    def _build_completion_history(
        self, messages: Sequence[dict[str, Any]], system_message: str
    ) -> list[dict[str, str]]:
        history: list[dict[str, str]] = []
        if system_message:
            history.append({"role": "system", "content": system_message})
        for message in messages:
            content = message.get("content")
            if not content or "tool_calls" in message or "tool_responses" in message:
                continue
            history.append({"role": self._normalize_chat_role(message), "content": str(content)})
        return history

    def _normalize_chat_role(self, message: dict[str, Any]) -> str:
        role = str(message.get("role") or "").lower()
        if role in {"system", "assistant", "user"}:
            return role
        return "assistant" if message.get("name") == "assistant" else "user"

    def _run_async(self, coro: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()
