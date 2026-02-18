from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SessionEntry:
    type: str
    content: str
    tool: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": self.type,
            "ts": datetime.now(timezone.utc).isoformat(),
            "content": self.content,
        }
        if self.tool is not None:
            data["tool"] = self.tool
        return data


class SessionService:
    def __init__(self, sessions_dir: Path) -> None:
        self.sessions_dir = sessions_dir

    def normalize_session_id(self, session_id: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id).strip("-")
        return cleaned[:64] or "default"

    def _session_path(self, session_id: str) -> Path:
        safe_session = self.normalize_session_id(session_id)
        return self.sessions_dir / f"{safe_session}.json"

    def load(self, session_id: str) -> list[dict[str, Any]]:
        path = self._session_path(session_id)
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        return raw

    def save(self, session_id: str, entries: list[dict[str, Any]]) -> None:
        path = self._session_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    def append(self, session_id: str, new_entries: list[SessionEntry]) -> None:
        entries = self.load(session_id)
        entries.extend(item.to_dict() for item in new_entries)
        self.save(session_id, entries)

    def list_sessions(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for file_path in sorted(self.sessions_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            stat = file_path.stat()
            result.append(
                {
                    "id": file_path.stem,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "size_bytes": stat.st_size,
                }
            )
        return result

    def to_chat_messages(self, session_id: str, max_messages: int = 30) -> list[dict[str, str]]:
        history = self.load(session_id)
        messages: list[dict[str, str]] = []
        for item in history:
            role = item.get("type")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({"role": role, "content": content})
        return messages[-max_messages:]
