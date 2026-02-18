from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from backend.services.knowledge_service import KnowledgeService


def create_search_knowledge_tool(knowledge_service: KnowledgeService) -> BaseTool:
    @tool("search_knowledge_base")
    def search_knowledge_base(query: str) -> str:
        """Search local knowledge base with hybrid retrieval (BM25 + vector)."""
        return knowledge_service.search(query)

    return search_knowledge_base
