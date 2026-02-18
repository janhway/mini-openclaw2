from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TRUNCATED_MARKER = "...[truncated]"


@dataclass(frozen=True)
class PromptFileSpec:
    name: str
    path: Path
    max_chars: int


class PromptService:
    def __init__(self, workspace_dir: Path, memory_file: Path) -> None:
        self.workspace_dir = workspace_dir
        self.memory_file = memory_file

    def _truncate(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        allowed = max(0, max_chars - len(TRUNCATED_MARKER))
        return f"{text[:allowed]}{TRUNCATED_MARKER}"

    def _read_with_budget(self, spec: PromptFileSpec) -> str:
        if not spec.path.exists():
            return ""
        text = spec.path.read_text(encoding="utf-8")
        return self._truncate(text, spec.max_chars)

    def build_system_prompt(self) -> str:
        specs = [
            PromptFileSpec("SKILLS_SNAPSHOT.md", self.workspace_dir / "SKILLS_SNAPSHOT.md", 10_000),
            PromptFileSpec("SOUL.md", self.workspace_dir / "SOUL.md", 9_000),
            PromptFileSpec("IDENTITY.md", self.workspace_dir / "IDENTITY.md", 9_000),
            PromptFileSpec("USER.md", self.workspace_dir / "USER.md", 7_000),
            PromptFileSpec("AGENTS.md", self.workspace_dir / "AGENTS.md", 7_000),
            PromptFileSpec("MEMORY.md", self.memory_file, 5_000),
        ]

        parts: list[str] = []
        for spec in specs:
            content = self._read_with_budget(spec)
            section = f"# {spec.name}\n{content}" if content else f"# {spec.name}\n"
            parts.append(section)

        prompt = "\n\n".join(parts)
        if len(prompt) > 50_000:
            allowed = 50_000 - len(TRUNCATED_MARKER)
            prompt = f"{prompt[:allowed]}{TRUNCATED_MARKER}"
        return prompt
