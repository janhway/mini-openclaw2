import { Save } from "lucide-react";

import { MonacoEditor } from "@/components/editor/monaco-editor";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";

interface InspectorProps {
  selectedPath: string;
  pathOptions: string[];
  editorContent: string;
  saving: boolean;
  onPathChange: (path: string) => void;
  onContentChange: (value: string) => void;
  onSave: () => void;
}

export function Inspector({
  selectedPath,
  pathOptions,
  editorContent,
  saving,
  onPathChange,
  onContentChange,
  onSave,
}: InspectorProps) {
  return (
    <Panel className="flex h-full flex-col p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-800">文件编辑器</h2>
        <Button onClick={onSave} disabled={saving} className="gap-1.5">
          <Save className="h-4 w-4" />
          {saving ? "保存中..." : "保存"}
        </Button>
      </div>

      <select
        value={selectedPath}
        onChange={(event) => onPathChange(event.target.value)}
        className="mb-3 h-10 rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-blue-500/40"
      >
        {pathOptions.map((path) => (
          <option value={path} key={path}>
            {path}
          </option>
        ))}
      </select>

      <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-slate-200">
        <MonacoEditor value={editorContent} onChange={onContentChange} />
      </div>
    </Panel>
  );
}
