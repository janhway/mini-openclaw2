from __future__ import annotations

import shlex
from pathlib import Path

from langchain_community.tools import ShellTool
from langchain_core.tools import BaseTool, tool

DANGEROUS_PATTERNS = (
    "rm -rf /",
    "mkfs",
    "dd if=",
    "shutdown",
    "reboot",
    "poweroff",
    ":(){",
)


def create_terminal_tool(root_dir: Path) -> BaseTool:
    shell_tool = ShellTool()

    @tool("terminal")
    def terminal(command: str) -> str:
        """Execute shell commands in backend root with safety guards."""
        normalized = command.strip()
        if not normalized:
            return "No command provided."

        lower = normalized.lower()
        if any(pattern in lower for pattern in DANGEROUS_PATTERNS):
            return "Blocked dangerous command pattern."
        if ".." in normalized:
            return "Blocked path traversal pattern in command."

        wrapped = f"cd {shlex.quote(str(root_dir))} && {normalized}"
        result = shell_tool.invoke({"commands": [wrapped]})
        text = str(result)
        if len(text) > 8_000:
            return f"{text[:7990]}...[truncated]"
        return text

    return terminal
