/**
 * useChat hook - Chat functionality with streaming responses.
 * Implements FRD 14 (Chatbot) Section 12 - Cross-Page Persistence.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { getChatHistory } from "@/services/api";
import { createChatStream } from "@/services/chatSSE";
import type { ChatMessage, Citation } from "@/types/chat";

export interface UseChatReturn {
  /** All messages in the conversation */
  messages: ChatMessage[];
  /** Whether a response is currently streaming */
  isStreaming: boolean;
  /** Current partial response during streaming */
  currentResponse: string;
  /** Error message, if any */
  error: string | null;
  /** Whether the chat history is loading */
  isLoading: boolean;
  /** Send a message to the chatbot */
  sendMessage: (message: string) => void;
  /** Clear the error state */
  clearError: () => void;
}

/**
 * Hook for managing chat state and streaming responses.
 *
 * @param reportId - The report to chat about
 * @returns Chat state and actions
 */
export function useChat(reportId: string | undefined): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Track current citations during streaming
  const currentCitationsRef = useRef<Citation[]>([]);
  // Abort controller for cancelling streams
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load conversation history on mount or reportId change
  useEffect(() => {
    if (!reportId) {
      setMessages([]);
      return;
    }

    let cancelled = false;

    async function loadHistory() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await getChatHistory(reportId!);
        if (!cancelled) {
          setMessages(response.messages);
        }
      } catch (err) {
        if (!cancelled) {
          // Don't show error for empty history (404)
          const errorMessage = err instanceof Error ? err.message : "Failed to load chat history";
          if (!errorMessage.includes("404")) {
            setError(errorMessage);
          }
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      cancelled = true;
    };
  }, [reportId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const sendMessage = useCallback(
    (message: string) => {
      if (!reportId || isStreaming || !message.trim()) {
        return;
      }

      setError(null);
      setIsStreaming(true);
      setCurrentResponse("");
      currentCitationsRef.current = [];

      // Add user message immediately
      const userMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: message,
        citations: [],
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Create the streaming connection
      abortControllerRef.current = createChatStream(reportId, message, {
        onToken: (token) => {
          setCurrentResponse((prev) => prev + token);
        },
        onCitations: (citations) => {
          currentCitationsRef.current = citations;
        },
        onDone: (messageId, fullContent) => {
          // Add assistant message with full content and citations
          const assistantMessage: ChatMessage = {
            id: messageId,
            role: "assistant",
            content: fullContent,
            citations: currentCitationsRef.current,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setIsStreaming(false);
          setCurrentResponse("");
          currentCitationsRef.current = [];
        },
        onError: (errorMessage) => {
          setError(errorMessage);
          setIsStreaming(false);
          setCurrentResponse("");
        },
      });
    },
    [reportId, isStreaming]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isStreaming,
    currentResponse,
    error,
    isLoading,
    sendMessage,
    clearError,
  };
}
