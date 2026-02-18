from __future__ import annotations

from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage

from backend.config import ModelSettings
from backend.services.agent_service import AgentService
from backend.services.prompt_service import PromptService
from backend.services.session_service import SessionService
from backend.services.skill_service import SkillService


def _service() -> AgentService:
    root = Path("backend")
    return AgentService(
        model_settings=ModelSettings(
            base_url="https://api.deepseek.com/v1",
            api_key="sk-test",
            model="deepseek-chat",
        ),
        prompt_service=PromptService(workspace_dir=root / "workspace", memory_file=root / "memory" / "MEMORY.md"),
        skill_service=SkillService(skills_dir=root / "skills", workspace_dir=root / "workspace", root_dir=root),
        session_service=SessionService(sessions_dir=root / "sessions"),
        tools=[],
    )


def test_extract_final_text_ignores_tool_messages() -> None:
    service = _service()
    output = {
        "messages": [
            ToolMessage(content="---\\nname: get_weather\\n...", tool_call_id="call_1"),
            AIMessage(content="莆田当前天气多云，气温 10.7°C。"),
        ]
    }
    final = service._extract_final_text(output)
    assert "莆田" in final
    assert "10.7" in final


def test_extract_final_text_returns_empty_when_only_tool_messages() -> None:
    service = _service()
    output = {
        "messages": [
            ToolMessage(content="tool output only", tool_call_id="call_2"),
        ]
    }
    final = service._extract_final_text(output)
    assert final == ""
