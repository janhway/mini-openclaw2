import { ChatEvent } from "@/types";

function parseSseBlock(block: string): ChatEvent | null {
  const lines = block.split("\n");
  let eventType = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  try {
    const parsed = JSON.parse(dataLines.join("\n")) as ChatEvent;
    if (!parsed.type) {
      parsed.type = eventType as ChatEvent["type"];
    }
    return parsed;
  } catch {
    return {
      type: (eventType as ChatEvent["type"]) ?? "error",
      content: dataLines.join("\n"),
    };
  }
}

export async function streamSse(
  response: Response,
  onEvent: (event: ChatEvent) => void,
): Promise<void> {
  if (!response.body) {
    throw new Error("SSE 响应体为空");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const parsed = parseSseBlock(block.trim());
      if (parsed) {
        onEvent(parsed);
      }
    }
  }

  if (buffer.trim()) {
    const parsed = parseSseBlock(buffer.trim());
    if (parsed) {
      onEvent(parsed);
    }
  }
}
