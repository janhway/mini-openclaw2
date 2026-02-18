import { Wrench, Bot, CircleAlert, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { TimelineItem } from "@/types";

interface StageProps {
  timeline: TimelineItem[];
  input: string;
  sending: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
}

export function Stage({ timeline, input, sending, onInputChange, onSend }: StageProps) {
  return (
    <Panel className="flex h-full flex-col p-4 md:p-5">
      <div className="mb-4 border-b border-slate-200/70 pb-3 text-sm font-semibold text-slate-800">对话区</div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {timeline.map((item) => {
          if (item.kind === "thought") {
            return (
              <details key={item.id} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                <summary className="cursor-pointer text-xs font-semibold text-slate-600">思考过程</summary>
                <div className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{item.content}</div>
              </details>
            );
          }

          if (item.kind === "tool_call" || item.kind === "tool_result") {
            return (
              <div key={item.id} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">
                <div className="flex items-center gap-2 text-slate-700">
                  <Wrench className="h-4 w-4" />
                  <span className="font-semibold">{item.kind === "tool_call" ? "工具调用" : "工具结果"}</span>
                  {item.name ? <span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{item.name}</span> : null}
                </div>
                <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-slate-600">
                  {JSON.stringify(item.payload ?? item.content, null, 2)}
                </pre>
              </div>
            );
          }

          if (item.kind === "error") {
            return (
              <div key={item.id} className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                <div className="mb-1 flex items-center gap-2 font-semibold"><CircleAlert className="h-4 w-4" /> 错误</div>
                <div className="whitespace-pre-wrap">{item.content}</div>
              </div>
            );
          }

          return (
            <div key={item.id} className={`rounded-xl px-3 py-2 text-sm ${item.kind === "user" ? "bg-[var(--accent-blue)] text-white" : "bg-slate-100 text-slate-800"}`}>
              <div className="mb-1 flex items-center gap-2 text-xs font-semibold opacity-80">
                {item.kind === "user" ? <UserRound className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                {item.kind === "user" ? "你" : "助手"}
              </div>
              <div className="whitespace-pre-wrap">{item.content}</div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex gap-2 border-t border-slate-200/70 pt-3">
        <textarea
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              if (!sending) {
                onSend();
              }
            }
          }}
          placeholder="请输入你的问题..."
          className="h-24 flex-1 resize-none rounded-xl border border-slate-300 bg-white/90 p-3 text-sm text-slate-800 outline-none ring-blue-500/30 placeholder:text-slate-400 focus:ring"
        />
        <Button className="h-10 self-end" onClick={onSend} disabled={sending || !input.trim()}>
          {sending ? "生成中..." : "发送"}
        </Button>
      </div>
    </Panel>
  );
}
