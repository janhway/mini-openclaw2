from __future__ import annotations

from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_experimental.tools import PythonREPLTool

from backend.services.knowledge_service import KnowledgeService
from backend.tools.fetch_tool import create_fetch_url_tool
from backend.tools.file_tool import create_read_file_tool
from backend.tools.kb_tool import create_search_knowledge_tool
from backend.tools.terminal_tool import create_terminal_tool


def build_core_tools(root_dir: Path, knowledge_service: KnowledgeService) -> list[BaseTool]:
    return [
        create_terminal_tool(root_dir=root_dir),
        PythonREPLTool(),
        create_fetch_url_tool(),
        create_read_file_tool(root_dir=root_dir),
        create_search_knowledge_tool(knowledge_service=knowledge_service),
    ]
