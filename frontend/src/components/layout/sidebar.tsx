import { MessageSquare, Brain, Library, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { SessionSummary } from "@/types";

interface SidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onReloadSessions: () => void;
}

export function Sidebar({ sessions, activeSessionId, onSelectSession, onReloadSessions }: SidebarProps) {
  return (
    <Panel className="flex h-full flex-col p-4">
      <div className="mb-4 space-y-2">
        <div className="flex items-center gap-2 text-slate-800">
          <MessageSquare className="h-4 w-4" />
          <span className="text-sm font-semibold">Workspace</span>
        </div>
        <div className="space-y-1 text-xs text-slate-600">
          <div className="flex items-center gap-2"><Brain className="h-3.5 w-3.5" /> Chat</div>
          <div className="flex items-center gap-2"><Library className="h-3.5 w-3.5" /> Memory / Skills</div>
        </div>
      </div>

      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-800">Sessions</h2>
        <Button variant="ghost" className="h-8 w-8 p-0" onClick={onReloadSessions}>
          <RefreshCcw className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto">
        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={`w-full rounded-xl border px-3 py-2 text-left transition-colors ${
              session.id === activeSessionId
                ? "border-[var(--accent-blue)] bg-[var(--accent-blue)]/10"
                : "border-white/50 bg-white/40 hover:bg-white/70"
            }`}
          >
            <div className="truncate text-sm font-medium text-slate-800">{session.id}</div>
            <div className="mt-1 text-[11px] text-slate-500">{new Date(session.updated_at).toLocaleString()}</div>
          </button>
        ))}
      </div>
    </Panel>
  );
}
