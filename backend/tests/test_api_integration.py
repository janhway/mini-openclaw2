from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_files_post_and_get_roundtrip(client: TestClient) -> None:
    path = "memory/test_integration_note.md"
    content = "integration-test-content"

    save_response = client.post("/api/files", json={"path": path, "content": content})
    assert save_response.status_code == 200
    assert save_response.json()["ok"] is True

    read_response = client.get("/api/files", params={"path": path})
    assert read_response.status_code == 200
    payload = read_response.json()
    assert payload["path"] == path
    assert payload["content"] == content

    # Cleanup test artifact.
    target = Path("backend") / path
    if target.exists():
        target.unlink()


def test_files_block_path_traversal(client: TestClient) -> None:
    response = client.get("/api/files", params={"path": "../KEY.md"})
    assert response.status_code == 400


def test_sessions_list_and_get_session(client: TestClient) -> None:
    session_id = "it-session"
    session_file = Path("backend/sessions/it-session.json")
    session_file.write_text(
        json.dumps(
            [
                {
                    "type": "user",
                    "ts": "2026-02-18T00:00:00Z",
                    "content": "hello",
                }
            ]
        ),
        encoding="utf-8",
    )

    list_response = client.get("/api/sessions")
    assert list_response.status_code == 200
    sessions = list_response.json()["sessions"]
    assert any(item["id"] == session_id for item in sessions)

    get_response = client.get(f"/api/sessions/{session_id}")
    assert get_response.status_code == 200
    assert get_response.json()["session_id"] == session_id
    assert get_response.json()["entries"][0]["content"] == "hello"

    if session_file.exists():
        session_file.unlink()


def test_chat_stream_sse(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    from backend import app as backend_app

    async def fake_stream_chat(message: str, session_id: str):
        assert message == "ping"
        assert session_id == "sse-it"
        yield {"type": "thought", "content": "thinking"}
        yield {"type": "tool_call", "name": "read_file", "input": {"path": "skills/get_weather/SKILL.md"}}
        yield {"type": "final", "content": "done"}

    monkeypatch.setattr(backend_app.agent_service, "stream_chat", fake_stream_chat)

    response = client.post(
        "/api/chat",
        json={"message": "ping", "session_id": "sse-it", "stream": True},
    )
    assert response.status_code == 200
    body = response.text
    assert "event: thought" in body
    assert "event: tool_call" in body
    assert "event: final" in body


def test_chat_weather_putian(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    from backend import app as backend_app

    async def fake_stream_chat(message: str, session_id: str):
        assert message == "今天莆田的天气如何"
        assert session_id == "weather-it"
        yield {"type": "thought", "content": "识别到天气查询，准备读取天气技能。"}
        yield {"type": "tool_call", "name": "read_file", "input": {"path": "skills/get_weather/SKILL.md"}}
        yield {
            "type": "final",
            "content": "莆田今天天气：多云，当前气温 26°C，体感 27°C，未来 24 小时有短时小雨。",
        }

    monkeypatch.setattr(backend_app.agent_service, "stream_chat", fake_stream_chat)

    response = client.post(
        "/api/chat",
        json={"message": "今天莆田的天气如何", "session_id": "weather-it", "stream": False},
    )
    assert response.status_code == 200

    events = response.json()["events"]
    final_event = next(event for event in events if event["type"] == "final")
    assert "莆田" in final_event["content"]
    assert "天气" in final_event["content"]
    assert "气温" in final_event["content"]
