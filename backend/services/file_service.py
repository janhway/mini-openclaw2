from __future__ import annotations

from pathlib import Path


class PathSecurityError(ValueError):
    """Raised when a path attempts to escape root_dir or violates policy."""


class FileService:
    def __init__(
        self,
        root_dir: Path,
        writable_prefixes: tuple[str, ...] = ("memory/", "skills/", "workspace/", "sessions/"),
    ) -> None:
        self.root_dir = root_dir.resolve()
        self.writable_prefixes = writable_prefixes

    def _normalize_relative_path(self, relative_path: str) -> str:
        path = relative_path.strip().replace("\\", "/")
        if not path:
            raise PathSecurityError("path cannot be empty")
        if path.startswith("/"):
            raise PathSecurityError("absolute paths are not allowed")
        if ".." in Path(path).parts:
            raise PathSecurityError("path traversal is not allowed")
        return path

    def resolve_safe_path(self, relative_path: str) -> Path:
        normalized = self._normalize_relative_path(relative_path)
        candidate = (self.root_dir / normalized).resolve()

        if self.root_dir == candidate:
            return candidate

        if self.root_dir not in candidate.parents:
            raise PathSecurityError("path escapes backend root")

        return candidate

    def can_write(self, relative_path: str) -> bool:
        normalized = self._normalize_relative_path(relative_path)
        return any(normalized.startswith(prefix) for prefix in self.writable_prefixes)

    def read_text(self, relative_path: str) -> str:
        target = self.resolve_safe_path(relative_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"file not found: {relative_path}")
        return target.read_text(encoding="utf-8")

    def write_text(self, relative_path: str, content: str) -> None:
        if not self.can_write(relative_path):
            raise PathSecurityError("write path is not allowed")

        target = self.resolve_safe_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
