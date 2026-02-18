import { useState } from "react";

import { streamChat } from "@/lib/api";
import { ChatEvent } from "@/types";

export function useChatStream(onEvent: (event: ChatEvent) => void) {
  const [sending, setSending] = useState(false);

  const sendMessage = async (message: string, sessionId: string) => {
    setSending(true);
    try {
      await streamChat(message, sessionId, onEvent);
    } finally {
      setSending(false);
    }
  };

  return { sending, sendMessage };
}
