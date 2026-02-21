/**
 * Chat SSE service for streaming chat responses.
 * Implements FRD 14 (Chatbot) Section 11 - Streaming Response Display.
 */

import { getChatMessageUrl } from "./api";
import type {
  Citation,
  ChatTokenEventData,
  ChatCitationsEventData,
  ChatDoneEventData,
  ChatErrorEventData,
} from "@/types/chat";

/**
 * Callbacks for chat stream events.
 */
export interface ChatStreamCallbacks {
  onToken: (token: string) => void;
  onCitations: (citations: Citation[]) => void;
  onDone: (messageId: string, fullContent: string) => void;
  onError: (error: string) => void;
}

/**
 * Parsed SSE line data.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface _SSELine {
  event?: string;
  data?: string;
  id?: string;
}

/**
 * Parse an SSE event block into event type and data.
 */
function parseSSEBlock(block: string): { eventType: string; data: unknown } | null {
  const lines = block.split("\n");
  let eventType = "message";
  let dataStr = "";

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      eventType = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      dataStr = line.slice(6);
    }
  }

  if (!dataStr) {
    return null;
  }

  try {
    const data = JSON.parse(dataStr);
    return { eventType, data };
  } catch {
    return null;
  }
}

/**
 * Create a streaming chat connection using fetch with ReadableStream.
 *
 * Since EventSource only supports GET requests, we use fetch with
 * ReadableStream to handle the POST request for sending the message.
 *
 * @param reportId - The report to chat about
 * @param message - The user's message
 * @param callbacks - Callbacks for handling stream events
 * @returns AbortController to cancel the stream
 */
export function createChatStream(
  reportId: string,
  message: string,
  callbacks: ChatStreamCallbacks
): AbortController {
  const abortController = new AbortController();
  const url = getChatMessageUrl(reportId);

  // Start the fetch request
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ message }),
    signal: abortController.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text();
        callbacks.onError(`HTTP ${response.status}: ${errorText}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError("No response body");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Split on double newlines to get complete SSE events
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || ""; // Keep the incomplete part in buffer

        for (const part of parts) {
          if (!part.trim()) continue;

          const parsed = parseSSEBlock(part);
          if (!parsed) continue;

          const { eventType, data } = parsed;

          switch (eventType) {
            case "chat_token": {
              const tokenData = data as ChatTokenEventData;
              callbacks.onToken(tokenData.token);
              break;
            }
            case "chat_citations": {
              const citationsData = data as ChatCitationsEventData;
              callbacks.onCitations(citationsData.citations);
              break;
            }
            case "chat_done": {
              const doneData = data as ChatDoneEventData;
              callbacks.onDone(doneData.message_id, doneData.full_content);
              break;
            }
            case "chat_error": {
              const errorData = data as ChatErrorEventData;
              callbacks.onError(errorData.error);
              break;
            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name === "AbortError") {
        // Stream was cancelled, ignore
        return;
      }
      callbacks.onError(error.message || "Stream connection failed");
    });

  return abortController;
}
