/**
 * ChatPanel component - Slide-out chatbot panel.
 * Implements FRD 14 (Chatbot) Section 8 - Chat Panel UI.
 */

import { useEffect, useRef, useCallback } from "react";
import { X, MessageSquare, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useChat } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import type { Citation, ChatMessage as ChatMessageType } from "@/types/chat";

interface ChatPanelProps {
  reportId: string | undefined;
  isOpen: boolean;
  onClose: () => void;
  onCitationClick?: (citation: Citation) => void;
}

export function ChatPanel({
  reportId,
  isOpen,
  onClose,
  onCitationClick,
}: ChatPanelProps) {
  const {
    messages,
    isStreaming,
    currentResponse,
    error,
    isLoading,
    sendMessage,
    clearError,
  } = useChat(reportId);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, currentResponse]);

  // Handle escape key to close panel
  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Handle citation click with navigation
  const handleCitationClick = useCallback(
    (citation: Citation) => {
      if (onCitationClick) {
        onCitationClick(citation);
      }
    },
    [onCitationClick]
  );

  // Create a temporary message for streaming response
  const streamingMessage: ChatMessageType | null = isStreaming && currentResponse
    ? {
        id: "streaming",
        role: "assistant",
        content: currentResponse,
        citations: [],
        timestamp: new Date().toISOString(),
      }
    : null;

  return (
    <>
      {/* Backdrop overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 dark:bg-black/40 z-40 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          "fixed top-0 right-0 h-full w-full sm:w-[420px] z-50",
          "bg-white dark:bg-gray-900",
          "shadow-2xl",
          "flex flex-col",
          "transform transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Chat with report"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Chat with Report
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 
                       text-gray-500 dark:text-gray-400 transition-colors"
            aria-label="Close chat panel"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages container */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto"
        >
          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          )}

          {/* Empty state */}
          {!isLoading && messages.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center h-full px-6 text-center">
              <MessageSquare className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                Ask about this report
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs">
                Ask questions about the analysis results, claims, agent findings,
                IFRS compliance, or disclosure gaps.
              </p>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="mx-4 mt-4 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                  <button
                    onClick={clearError}
                    className="mt-2 text-sm text-red-600 dark:text-red-400 
                               hover:text-red-800 dark:hover:text-red-200 underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          {!isLoading && (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onCitationClick={handleCitationClick}
                />
              ))}
              
              {/* Streaming message */}
              {streamingMessage && (
                <ChatMessage
                  message={streamingMessage}
                  onCitationClick={handleCitationClick}
                  isStreaming
                />
              )}
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        {reportId && (
          <ChatInput
            onSend={sendMessage}
            disabled={isStreaming || !reportId}
            placeholder={
              isStreaming
                ? "Waiting for response..."
                : "Ask about the report..."
            }
          />
        )}

        {/* No report selected state */}
        {!reportId && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-center text-gray-500 dark:text-gray-400">
              Select a report to start chatting
            </p>
          </div>
        )}
      </div>
    </>
  );
}
