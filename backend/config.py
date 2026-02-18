from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class ModelSettings:
    base_url: str
    api_key: str
    model: str


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    backend_root: Path
    root_dir: Path
    memory_file: Path
    sessions_dir: Path
    skills_dir: Path
    workspace_dir: Path
    knowledge_dir: Path
    storage_dir: Path
    tmp_dir: Path
    model: ModelSettings


def _parse_key_md(path: Path) -> Dict[str, Dict[str, str]]:
    providers: Dict[str, Dict[str, str]] = {}
    current_provider = "default"
    providers[current_provider] = {}

    if not path.exists():
        return providers

    heading_pattern = re.compile(r"^##\s+\d+\.\d+\s+(.+)$")
    kv_pattern = re.compile(r"^(base_url|api_key|model)\s*=\s*\"([^\"]*)\"\s*$")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading_match = heading_pattern.match(line)
        if heading_match:
            provider_name = heading_match.group(1).strip().split()[0].lower()
            current_provider = provider_name
            providers.setdefault(current_provider, {})
            continue

        kv_match = kv_pattern.match(line)
        if kv_match:
            key, value = kv_match.groups()
            providers[current_provider][key] = value

    return providers


def _resolve_model_settings(project_root: Path) -> ModelSettings:
    provider = os.getenv("MODEL_PROVIDER", "deepseek").lower().strip()
    providers = _parse_key_md(project_root / "KEY.md")
    provider_config = providers.get(provider) or providers.get("default", {})

    base_url = os.getenv("OPENAI_BASE_URL", provider_config.get("base_url", ""))
    api_key = os.getenv("OPENAI_API_KEY", provider_config.get("api_key", ""))
    model = os.getenv("OPENAI_MODEL", provider_config.get("model", ""))

    return ModelSettings(base_url=base_url, api_key=api_key, model=model)


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    project_root = Path(__file__).resolve().parents[1]
    backend_root = project_root / "backend"

    return AppConfig(
        project_root=project_root,
        backend_root=backend_root,
        root_dir=backend_root,
        memory_file=backend_root / "memory" / "MEMORY.md",
        sessions_dir=backend_root / "sessions",
        skills_dir=backend_root / "skills",
        workspace_dir=backend_root / "workspace",
        knowledge_dir=backend_root / "knowledge",
        storage_dir=backend_root / "storage",
        tmp_dir=project_root / "tmp",
        model=_resolve_model_settings(project_root),
    )


def ensure_runtime_dirs(config: AppConfig) -> None:
    required_dirs = [
        config.backend_root,
        config.memory_file.parent,
        config.memory_file.parent / "logs",
        config.sessions_dir,
        config.skills_dir,
        config.workspace_dir,
        config.knowledge_dir,
        config.storage_dir,
        config.tmp_dir,
    ]
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)
