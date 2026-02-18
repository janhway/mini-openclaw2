from __future__ import annotations

import json
import logging
import os
from typing import Any, AsyncIterator

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from backend.config import ModelSettings
from backend.services.prompt_service import PromptService
from backend.services.session_service import SessionEntry, SessionService
from backend.services.skill_service import SkillService

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(
        self,
        model_settings: ModelSettings,
        prompt_service: PromptService,
        skill_service: SkillService,
        session_service: SessionService,
        tools: list[Any],
    ) -> None:
        self.model_settings = model_settings
        self.prompt_service = prompt_service
        self.skill_service = skill_service
        self.session_service = session_service
        self.tools = tools

    def _resolve_runtime_model(self) -> tuple[str, str | None]:
        configured = self.model_settings.model
        tool_model_override = os.getenv("OPENAI_TOOL_MODEL", "").strip()
        if tool_model_override:
            return tool_model_override, configured

        base = (self.model_settings.base_url or "").lower()
        if "deepseek.com" in base and configured == "deepseek-reasoner":
            return "deepseek-chat", configured

        return configured, None

    def _build_agent(self, system_prompt: str):
        runtime_model, _ = self._resolve_runtime_model()
        model = ChatOpenAI(
            model=runtime_model,
            api_key=self.model_settings.api_key,
            base_url=self.model_settings.base_url or None,
            temperature=0,
        )
        return create_agent(model=model, tools=self.tools, system_prompt=system_prompt), runtime_model

    def _extract_chunk_text(self, chunk: Any) -> str:
        if chunk is None:
            return ""
        if isinstance(chunk, str):
            return chunk

        content = getattr(chunk, "content", None)
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            output_parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    output_parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        output_parts.append(text)
            return "".join(output_parts)

        if isinstance(chunk, dict):
            text = chunk.get("text")
            if isinstance(text, str):
                return text

        return ""

    def _extract_final_text(self, output: Any) -> str:
        if output is None:
            return ""

        if isinstance(output, str):
            return output

        if isinstance(output, dict):
            messages = output.get("messages")
            if isinstance(messages, list) and messages:
                for message in reversed(messages):
                    if not self._is_assistant_message(message):
                        continue
                    if self._has_tool_calls(message):
                        continue
                    content = self._message_content(message).strip()
                    if content:
                        return content

            output_text = output.get("output") or output.get("output_text")
            if isinstance(output_text, str):
                return output_text

        return ""

    def _is_assistant_message(self, message: Any) -> bool:
        if isinstance(message, dict):
            message_type = str(message.get("type") or message.get("role") or "").lower()
            return message_type in {"ai", "assistant"}
        message_type = str(getattr(message, "type", "")).lower()
        return message_type in {"ai", "assistant"}

    def _has_tool_calls(self, message: Any) -> bool:
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls")
            return isinstance(tool_calls, list) and len(tool_calls) > 0
        tool_calls = getattr(message, "tool_calls", None)
        return isinstance(tool_calls, list) and len(tool_calls) > 0

    def _message_content(self, message: Any) -> str:
        if isinstance(message, dict):
            content = message.get("content", "")
        else:
            content = getattr(message, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and isinstance(block.get("text"), str):
                    parts.append(block["text"])
            return "".join(parts)
        return str(content)

    def _shorten(self, value: Any, max_chars: int = 2_000) -> str:
        if value is None:
            raw = ""
        elif isinstance(value, str):
            raw = value
        else:
            try:
                raw = json.dumps(value, ensure_ascii=False, default=str)
            except Exception:
                raw = str(value)
        if len(raw) <= max_chars:
            return raw
        return f"{raw[: max_chars - 14]}...[truncated]"

    async def stream_chat(self, message: str, session_id: str) -> AsyncIterator[dict[str, Any]]:
        session = self.session_service.normalize_session_id(session_id)

        if not self.model_settings.model or not self.model_settings.api_key:
            yield {
                "type": "error",
                "content": "Model config is missing. Set OPENAI_MODEL / OPENAI_API_KEY or configure KEY.md provider.",
            }
            return

        self.skill_service.refresh_snapshot()
        system_prompt = self.prompt_service.build_system_prompt()
        history = self.session_service.to_chat_messages(session)
        agent, runtime_model = self._build_agent(system_prompt)

        pending_entries: list[SessionEntry] = [SessionEntry(type="user", content=message)]
        tool_call_cache: dict[str, dict[str, Any]] = {}
        final_text = ""
        final_emitted = False

        yield {"type": "thought", "content": "已加载技能快照与系统提示，开始执行。"}
        if runtime_model != self.model_settings.model:
            yield {
                "type": "thought",
                "content": f"检测到当前模型与工具链兼容性问题，已自动切换为 {runtime_model} 执行。",
            }

        try:
            async for event in agent.astream_events(
                {"messages": [*history, {"role": "user", "content": message}]},
                version="v2",
            ):
                event_type = event.get("event")
                data = event.get("data") or {}
                run_id = str(event.get("run_id") or "")

                if event_type == "on_chat_model_stream":
                    text = self._extract_chunk_text(data.get("chunk"))
                    if text:
                        yield {"type": "thought", "content": text}
                    continue

                if event_type == "on_tool_start":
                    tool_name = str(event.get("name") or data.get("name") or "tool")
                    tool_input = data.get("input") or {}
                    tool_call_cache[run_id] = {"name": tool_name, "input": tool_input}
                    pending_entries.append(
                        SessionEntry(
                            type="tool",
                            content=f"{tool_name} called",
                            tool={"name": tool_name, "input": tool_input},
                        )
                    )
                    yield {"type": "tool_call", "name": tool_name, "input": tool_input}
                    continue

                if event_type == "on_tool_end":
                    cached = tool_call_cache.get(run_id, {})
                    tool_name = str(cached.get("name") or event.get("name") or "tool")
                    output = data.get("output")
                    output_text = self._shorten(output)
                    pending_entries.append(
                        SessionEntry(
                            type="tool",
                            content=f"{tool_name} result",
                            tool={
                                "name": tool_name,
                                "input": cached.get("input", {}),
                                "output": output_text,
                            },
                        )
                    )
                    yield {"type": "tool_result", "name": tool_name, "output": output_text}
                    continue

                if event_type == "on_chain_end" and not final_emitted:
                    maybe_final = self._extract_final_text(data.get("output"))
                    if maybe_final.strip():
                        final_text = maybe_final
                        final_emitted = True
                        yield {"type": "final", "content": final_text}

        except Exception as exc:
            logger.exception("Agent streaming failed")
            error_text = str(exc)
            pending_entries.append(SessionEntry(type="assistant", content=error_text))
            self.session_service.append(session, pending_entries)
            yield {"type": "error", "content": error_text}
            return

        if not final_emitted:
            final_text = final_text or "未生成最终回复。"
            yield {"type": "final", "content": final_text}

        pending_entries.append(SessionEntry(type="assistant", content=final_text))
        self.session_service.append(session, pending_entries)
