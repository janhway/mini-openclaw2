from __future__ import annotations

from pathlib import Path

import pytest

from backend.config import ModelSettings
from backend.services.agent_service import AgentService
from backend.services.prompt_service import PromptService
from backend.services.session_service import SessionService
from backend.services.skill_service import SkillService


def _build_service(model_settings: ModelSettings) -> AgentService:
    root = Path("backend")
    return AgentService(
        model_settings=model_settings,
        prompt_service=PromptService(workspace_dir=root / "workspace", memory_file=root / "memory" / "MEMORY.md"),
        skill_service=SkillService(skills_dir=root / "skills", workspace_dir=root / "workspace", root_dir=root),
        session_service=SessionService(sessions_dir=root / "sessions"),
        tools=[],
    )


def test_deepseek_reasoner_auto_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_TOOL_MODEL", raising=False)
    service = _build_service(
        ModelSettings(
            base_url="https://api.deepseek.com/v1",
            api_key="sk-test",
            model="deepseek-reasoner",
        )
    )

    runtime_model, original_model = service._resolve_runtime_model()
    assert runtime_model == "deepseek-chat"
    assert original_model == "deepseek-reasoner"


def test_openai_tool_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_TOOL_MODEL", "custom-tool-model")
    service = _build_service(
        ModelSettings(
            base_url="https://api.deepseek.com/v1",
            api_key="sk-test",
            model="deepseek-reasoner",
        )
    )

    runtime_model, original_model = service._resolve_runtime_model()
    assert runtime_model == "custom-tool-model"
    assert original_model == "deepseek-reasoner"
