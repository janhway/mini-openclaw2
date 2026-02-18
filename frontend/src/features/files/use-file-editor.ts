import { useCallback, useState } from "react";

import { readFile, saveFile } from "@/lib/api";

export function useFileEditor(initialPath: string) {
  const [selectedPath, setSelectedPath] = useState(initialPath);
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async (path: string) => {
    const next = await readFile(path);
    setSelectedPath(path);
    setContent(next);
  }, []);

  const save = useCallback(async () => {
    setSaving(true);
    try {
      await saveFile(selectedPath, content);
    } finally {
      setSaving(false);
    }
  }, [content, selectedPath]);

  return {
    selectedPath,
    content,
    saving,
    setContent,
    load,
    save,
  };
}
