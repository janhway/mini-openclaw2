"use client";

import { useEffect, useMemo, useState } from "react";

import { Inspector } from "@/components/layout/inspector";
import { Navbar } from "@/components/layout/navbar";
import { Sidebar } from "@/components/layout/sidebar";
import { Stage } from "@/components/layout/stage";
import { createSession, getSession, readFile } from "@/lib/api";
import { useChatStream } from "@/features/chat/use-chat-stream";
import { useFileEditor } from "@/features/files/use-file-editor";
import { useSessions } from "@/features/sessions/use-sessions";
import { ChatEvent, TimelineItem } from "@/types";

const DEFAULT_EDITOR_PATH = "memory/MEMORY.md";

function eventToTimelineItem(event: ChatEvent): TimelineItem {
  if (event.type === "thought") {
    return {
      id: `${Date.now()}-${Math.random()}`,
      kind: "thought",
      content: event.content,
    };
  }

  if (event.type === "tool_call") {
    return {
      id: `${Date.now()}-${Math.random()}`,
      kind: "tool_call",
      name: event.name,
      payload: event.input,
    };
  }

  if (event.type === "tool_result") {
    return {
      id: `${Date.now()}-${Math.random()}`,
      kind: "tool_result",
      name: event.name,
      payload: event.output,
    };
  }

  if (event.type === "error") {
    return {
      id: `${Date.now()}-${Math.random()}`,
      kind: "error",
      content: event.content,
    };
  }

  return {
    id: `${Date.now()}-${Math.random()}`,
    kind: "assistant",
    content: event.content,
  };
}

function parseSkillPaths(snapshotContent: string): string[] {
  const matches = [...snapshotContent.matchAll(/<location>([^<]+)<\/location>/g)];
  return matches.map((match) => match[1]).filter(Boolean);
}

function appendEventToTimeline(current: TimelineItem[], event: ChatEvent): TimelineItem[] {
  if (event.type === "thought") {
    const rawChunk = event.content ?? "";
    if (!rawChunk.trim()) {
      return current;
    }

    const last = current[current.length - 1];
    if (last?.kind === "thought") {
      const merged = `${last.content ?? ""}${rawChunk}`;
      return [...current.slice(0, -1), { ...last, content: merged }];
    }
  }

  return [...current, eventToTimelineItem(event)];
}

export default function Home() {
  const { sessions, reloadSessions } = useSessions();
  const fileEditor = useFileEditor(DEFAULT_EDITOR_PATH);

  const [activeSessionId, setActiveSessionId] = useState("default");
  const [activeTab, setActiveTab] = useState<"memory" | "skills" | null>(null);
  const [input, setInput] = useState("");
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [skillPaths, setSkillPaths] = useState<string[]>([]);

  const onChatEvent = (event: ChatEvent) => {
    setTimeline((current) => appendEventToTimeline(current, event));
  };

  const { sending, sendMessage } = useChatStream(onChatEvent);

  const pathOptions = useMemo(() => {
    const base = ["memory/MEMORY.md", "workspace/AGENTS.md", "workspace/SOUL.md", "workspace/IDENTITY.md", "workspace/USER.md"];
    return [...new Set([...base, ...skillPaths])];
  }, [skillPaths]);

  const loadSessionToTimeline = async (sessionId: string) => {
    const entries = await getSession(sessionId);
    const restored: TimelineItem[] = entries.map((entry) => {
      if (entry.type === "user") {
        return { id: `${entry.ts}-user`, kind: "user", content: entry.content };
      }
      if (entry.type === "assistant") {
        return { id: `${entry.ts}-assistant`, kind: "assistant", content: entry.content };
      }
      if (entry.type === "tool" && entry.tool?.output) {
        return {
          id: `${entry.ts}-tool-result`,
          kind: "tool_result",
          name: entry.tool.name,
          payload: entry.tool.output,
        };
      }
      return {
        id: `${entry.ts}-tool-call`,
        kind: "tool_call",
        name: entry.tool?.name,
        payload: entry.tool?.input,
      };
    });

    setTimeline(restored);
  };

  const initialize = async () => {
    const currentSessions = await reloadSessions();
    const preferredSession = currentSessions[0]?.id ?? "default";
    setActiveSessionId(preferredSession);

    try {
      const snapshot = await readFile("workspace/SKILLS_SNAPSHOT.md");
      setSkillPaths(parseSkillPaths(snapshot));
    } catch {
      setSkillPaths([]);
    }

    await fileEditor.load(DEFAULT_EDITOR_PATH);

    if (currentSessions.length > 0) {
      await loadSessionToTimeline(preferredSession);
    } else {
      setTimeline([]);
    }
  };

  useEffect(() => {
    void initialize();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!pathOptions.includes(fileEditor.selectedPath)) {
      return;
    }
    void fileEditor.load(fileEditor.selectedPath);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileEditor.selectedPath]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || sending) {
      return;
    }

    setTimeline((current) => [
      ...current,
      {
        id: `${Date.now()}-user-input`,
        kind: "user",
        content: trimmed,
      },
    ]);
    setInput("");

    await sendMessage(trimmed, activeSessionId);
    await reloadSessions();
  };

  const handleTabChange = async (tab: "memory" | "skills") => {
    setActiveTab(tab);
    if (tab === "memory") {
      await fileEditor.load("memory/MEMORY.md");
      return;
    }
    if (tab === "skills") {
      const firstSkill = skillPaths[0] ?? "workspace/SKILLS_SNAPSHOT.md";
      await fileEditor.load(firstSkill);
    }
  };

  const handleCreateSession = async () => {
    const sessionId = `session-${new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14)}`;
    await createSession(sessionId);
    setActiveSessionId(sessionId);
    setActiveTab(null);
    setTimeline([]);
    setInput("");
    await reloadSessions();
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto flex h-[calc(100vh-56px)] max-w-[1680px] flex-col gap-3 p-3 md:p-4 lg:grid lg:grid-cols-[300px_minmax(0,1fr)_420px]">
        <div className="min-h-[260px] lg:min-h-0">
          <Sidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            activeTab={activeTab}
            onTabChange={(tab) => {
              void handleTabChange(tab);
            }}
            onReloadSessions={() => {
              void reloadSessions();
            }}
            onCreateSession={() => {
              void handleCreateSession();
            }}
            onSelectSession={(sessionId) => {
              setActiveSessionId(sessionId);
              setActiveTab(null);
              void loadSessionToTimeline(sessionId);
            }}
          />
        </div>

        <div className="min-h-[420px] lg:min-h-0">
          <Stage timeline={timeline} input={input} sending={sending} onInputChange={setInput} onSend={() => void handleSend()} />
        </div>

        <div className="min-h-[360px] lg:min-h-0">
          <Inspector
            selectedPath={fileEditor.selectedPath}
            pathOptions={pathOptions}
            editorContent={fileEditor.content}
            saving={fileEditor.saving}
            onPathChange={(nextPath) => {
              void fileEditor.load(nextPath);
            }}
            onContentChange={fileEditor.setContent}
            onSave={() => {
              void fileEditor.save();
            }}
          />
        </div>
      </main>
    </div>
  );
}
