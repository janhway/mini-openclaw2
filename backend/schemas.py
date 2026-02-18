from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(default="default")
    stream: bool = True


class FileSaveRequest(BaseModel):
    path: str
    content: str
