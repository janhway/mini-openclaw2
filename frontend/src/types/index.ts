export type ChatEventType = "thought" | "tool_call" | "tool_result" | "final" | "error";

export interface ChatEvent {
  type: ChatEventType;
  content?: string;
  name?: string;
  input?: unknown;
  output?: string;
}

export interface SessionSummary {
  id: string;
  updated_at: string;
  size_bytes: number;
}

export interface SessionEntry {
  type: "user" | "assistant" | "tool";
  ts: string;
  content: string;
  tool?: {
    name: string;
    input?: unknown;
    output?: string;
  };
}

export interface TimelineItem {
  id: string;
  kind: "user" | "assistant" | "thought" | "tool_call" | "tool_result" | "error";
  content?: string;
  name?: string;
  payload?: unknown;
}
