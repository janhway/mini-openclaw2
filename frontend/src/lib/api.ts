import { ChatEvent, SessionEntry, SessionSummary } from "@/types";
import { streamSse } from "@/lib/sse";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8002";

export async function listSessions(): Promise<SessionSummary[]> {
  const response = await fetch(`${API_BASE}/api/sessions`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to load sessions");
  }
  const payload = await response.json();
  return payload.sessions ?? [];
}

export async function getSession(sessionId: string): Promise<SessionEntry[]> {
  const response = await fetch(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to load session entries");
  }
  const payload = await response.json();
  return payload.entries ?? [];
}

export async function readFile(path: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/files?path=${encodeURIComponent(path)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to read file");
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
    throw new Error("Failed to save file");
  }
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
    throw new Error(`Chat request failed: ${response.status}`);
  }

  await streamSse(response, onEvent);
}
