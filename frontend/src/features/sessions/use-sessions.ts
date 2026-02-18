import { useCallback, useState } from "react";

import { listSessions } from "@/lib/api";
import { SessionSummary } from "@/types";

export function useSessions() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  const reloadSessions = useCallback(async () => {
    const items = await listSessions();
    setSessions(items);
    return items;
  }, []);

  return { sessions, reloadSessions };
}
