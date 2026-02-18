from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.config import ensure_runtime_dirs, get_app_config
from backend.schemas import ChatRequest, FileSaveRequest
from backend.services.agent_service import AgentService
from backend.services.file_service import FileService, PathSecurityError
from backend.services.knowledge_service import KnowledgeService
from backend.services.prompt_service import PromptService
from backend.services.session_service import SessionService
from backend.services.skill_service import SkillService
from backend.tools import build_core_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = get_app_config()
ensure_runtime_dirs(config)

file_service = FileService(root_dir=config.root_dir)
skill_service = SkillService(skills_dir=config.skills_dir, workspace_dir=config.workspace_dir, root_dir=config.root_dir)
prompt_service = PromptService(workspace_dir=config.workspace_dir, memory_file=config.memory_file)
session_service = SessionService(sessions_dir=config.sessions_dir)
knowledge_service = KnowledgeService(
    knowledge_dir=config.knowledge_dir,
    storage_dir=config.storage_dir,
    model_settings=config.model,
)
core_tools = build_core_tools(root_dir=config.root_dir, knowledge_service=knowledge_service)
agent_service = AgentService(
    model_settings=config.model,
    prompt_service=prompt_service,
    skill_service=skill_service,
    session_service=session_service,
    tools=core_tools,
)

app = FastAPI(title="mini-openclaw-backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sse(payload: dict) -> str:
    event_name = str(payload.get("type", "message"))
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event_name}\ndata: {data}\n\n"


@app.on_event("startup")
async def on_startup() -> None:
    skill_service.refresh_snapshot()
    knowledge_service.initialize()
    logger.info("Backend initialized. root_dir=%s", config.root_dir)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    async def event_stream() -> AsyncIterator[str]:
        async for payload in agent_service.stream_chat(
            message=request.message,
            session_id=request.session_id,
        ):
            yield _sse(payload)

    if request.stream:
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    events = []
    async for payload in agent_service.stream_chat(message=request.message, session_id=request.session_id):
        events.append(payload)
    return JSONResponse({"events": events})


@app.get("/api/files")
async def get_file(path: str = Query(..., description="backend relative path, e.g. memory/MEMORY.md")):
    try:
        content = file_service.read_text(path)
        return {"path": path, "content": content}
    except PathSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/files")
async def save_file(payload: FileSaveRequest):
    try:
        file_service.write_text(payload.path, payload.content)
        return {"ok": True, "path": payload.path}
    except PathSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sessions")
async def list_sessions():
    return {"sessions": session_service.list_sessions()}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    safe_id = session_service.normalize_session_id(session_id)
    entries = session_service.load(safe_id)
    return {"session_id": safe_id, "entries": entries}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8002)
