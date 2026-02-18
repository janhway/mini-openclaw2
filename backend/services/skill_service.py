from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

import yaml


@dataclass
class SkillMeta:
    name: str
    description: str
    location: str


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    if len(lines) < 3:
        return {}

    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    if end_index is None:
        return {}

    raw = "\n".join(lines[1:end_index])
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        return {}
    return data


class SkillService:
    def __init__(self, skills_dir: Path, workspace_dir: Path, root_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.workspace_dir = workspace_dir
        self.root_dir = root_dir
        self.snapshot_path = workspace_dir / "SKILLS_SNAPSHOT.md"

    def scan(self) -> list[SkillMeta]:
        metas: list[SkillMeta] = []
        for skill_md in sorted(self.skills_dir.glob("*/SKILL.md")):
            text = skill_md.read_text(encoding="utf-8")
            meta = _parse_frontmatter(text)
            name = str(meta.get("name") or skill_md.parent.name).strip()
            description = str(meta.get("description") or "").strip()
            location = skill_md.relative_to(self.root_dir).as_posix()
            metas.append(SkillMeta(name=name, description=description, location=location))
        return metas

    def generate_snapshot_xml(self, skills: Iterable[SkillMeta]) -> str:
        blocks = ["<available_skills>"]
        for skill in skills:
            blocks.extend(
                [
                    "  <skill>",
                    f"    <name>{escape(skill.name)}</name>",
                    f"    <description>{escape(skill.description)}</description>",
                    f"    <location>{escape(skill.location)}</location>",
                    "  </skill>",
                ]
            )
        blocks.append("</available_skills>")
        return "\n".join(blocks)

    def refresh_snapshot(self) -> str:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        skills = self.scan()
        snapshot = self.generate_snapshot_xml(skills)
        self.snapshot_path.write_text(snapshot, encoding="utf-8")
        return snapshot
