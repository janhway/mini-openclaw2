from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from backend.config import ModelSettings

logger = logging.getLogger(__name__)

try:
    from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex, load_index_from_storage
    from llama_index.retrievers.bm25 import BM25Retriever
except Exception:  # pragma: no cover - import guard for environments without deps
    Settings = None
    SimpleDirectoryReader = None
    StorageContext = None
    VectorStoreIndex = None
    load_index_from_storage = None
    BM25Retriever = None


class KnowledgeService:
    def __init__(self, knowledge_dir: Path, storage_dir: Path, model_settings: ModelSettings) -> None:
        self.knowledge_dir = knowledge_dir
        self.storage_dir = storage_dir
        self.model_settings = model_settings
        self.vector_index: Any | None = None
        self.bm25_retriever: Any | None = None
        self.initialized = False

    def _configure_embeddings(self) -> None:
        if Settings is None:
            return
        if not self.model_settings.api_key:
            return
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding

            embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
            Settings.embed_model = OpenAIEmbedding(
                model=embed_model,
                api_key=self.model_settings.api_key,
                api_base=self.model_settings.base_url or None,
            )
        except Exception as exc:  # pragma: no cover - external dependency behavior
            logger.warning("Failed to configure embedding model: %s", exc)

    def initialize(self) -> None:
        if self.initialized:
            return

        self.initialized = True
        if SimpleDirectoryReader is None or StorageContext is None or VectorStoreIndex is None:
            logger.warning("LlamaIndex dependencies are unavailable; knowledge search will fallback")
            return

        self._configure_embeddings()
        docs = list(self.knowledge_dir.rglob("*.md")) + list(self.knowledge_dir.rglob("*.txt")) + list(
            self.knowledge_dir.rglob("*.pdf")
        )
        if not docs:
            return

        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            has_storage = any(self.storage_dir.iterdir())
            if has_storage:
                storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_dir))
                self.vector_index = load_index_from_storage(storage_context)
            else:
                reader = SimpleDirectoryReader(input_dir=str(self.knowledge_dir), recursive=True)
                documents = reader.load_data()
                self.vector_index = VectorStoreIndex.from_documents(documents)
                self.vector_index.storage_context.persist(persist_dir=str(self.storage_dir))

            if BM25Retriever is not None and self.vector_index is not None:
                self.bm25_retriever = BM25Retriever.from_defaults(
                    docstore=self.vector_index.docstore,
                    similarity_top_k=4,
                )
        except Exception as exc:  # pragma: no cover - external dependency behavior
            logger.warning("Failed to initialize knowledge index: %s", exc)
            self.vector_index = None
            self.bm25_retriever = None

    def _node_content(self, node_like: Any) -> str:
        node = getattr(node_like, "node", node_like)
        if hasattr(node, "get_content"):
            return str(node.get_content())
        text = getattr(node, "text", None)
        if text is not None:
            return str(text)
        return str(node)

    def search(self, query: str, top_k: int = 4) -> str:
        self.initialize()

        if not query.strip():
            return "Query is empty."

        if self.vector_index is None:
            return "Knowledge base unavailable or empty."

        try:
            vector_retriever = self.vector_index.as_retriever(similarity_top_k=top_k)
            vector_results = vector_retriever.retrieve(query)
        except Exception as exc:  # pragma: no cover - external dependency behavior
            logger.warning("Vector retrieval failed: %s", exc)
            vector_results = []

        try:
            bm25_results = self.bm25_retriever.retrieve(query) if self.bm25_retriever is not None else []
        except Exception as exc:  # pragma: no cover - external dependency behavior
            logger.warning("BM25 retrieval failed: %s", exc)
            bm25_results = []

        merged: list[str] = []
        seen: set[str] = set()
        for item in [*vector_results, *bm25_results]:
            content = self._node_content(item).strip()
            if content and content not in seen:
                seen.add(content)
                merged.append(content)

        if not merged:
            return "No relevant knowledge found."

        payload = "\n\n---\n\n".join(merged[:top_k])
        if len(payload) > 6_000:
            payload = f"{payload[:5990]}...[truncated]"
        return payload
