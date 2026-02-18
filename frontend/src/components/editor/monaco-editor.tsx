"use client";

import Editor from "@monaco-editor/react";

interface MonacoEditorProps {
  value: string;
  onChange: (next: string) => void;
}

export function MonacoEditor({ value, onChange }: MonacoEditorProps) {
  return (
    <Editor
      height="100%"
      defaultLanguage="markdown"
      value={value}
      theme="vs"
      options={{
        minimap: { enabled: false },
        fontSize: 13,
        lineNumbersMinChars: 3,
        padding: { top: 10 },
        smoothScrolling: true,
      }}
      onChange={(next) => onChange(next ?? "")}
    />
  );
}
