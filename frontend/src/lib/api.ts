import { ChatEvent, SessionEntry, SessionSummary } from "@/types";
import { streamSse } from "@/lib/sse";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8002";

export async function listSessions(): Promise<SessionSummary[]> {
  const response = await fetch(`${API_BASE}/api/sessions`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("加载会话列表失败");
  }
  const payload = await response.json();
  return payload.sessions ?? [];
}

export async function getSession(sessionId: string): Promise<SessionEntry[]> {
  const response = await fetch(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("加载会话内容失败");
  }
  const payload = await response.json();
  return payload.entries ?? [];
}

export async function readFile(path: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/files?path=${encodeURIComponent(path)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("读取文件失败");
  }
  const payload = await response.json();
  return payload.content ?? "";
}

export async function saveFile(path: string, content: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/files`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, content }),
  });

  if (!response.ok) {
    throw new Error("保存文件失败");
  }
}

export async function createSession(sessionId: string): Promise<void> {
  await saveFile(`sessions/${sessionId}.json`, "[]");
}

export async function streamChat(
  message: string,
  sessionId: string,
  onEvent: (event: ChatEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, stream: true }),
  });

  if (!response.ok) {
    throw new Error(`对话请求失败：${response.status}`);
  }

  await streamSse(response, onEvent);
}
