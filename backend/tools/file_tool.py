from __future__ import annotations

from pathlib import Path

from langchain_community.tools.file_management import ReadFileTool
from langchain_core.tools import BaseTool


def create_read_file_tool(root_dir: Path) -> BaseTool:
    return ReadFileTool(root_dir=str(root_dir))
