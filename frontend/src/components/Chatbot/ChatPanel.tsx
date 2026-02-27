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

export function ChatPanel({ reportId, isOpen, onClose, onCitationClick }: ChatPanelProps) {
  const { messages, isStreaming, currentResponse, error, isLoading, sendMessage, clearError } =
    useChat(reportId);

  const messagesEndRef       = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentResponse]);

  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) onClose();
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  const handleCitationClick = useCallback(
    (citation: Citation) => onCitationClick?.(citation),
    [onCitationClick]
  );

  const streamingMessage: ChatMessageType | null =
    isStreaming && currentResponse
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
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/10 z-40 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          "fixed top-0 right-0 h-full w-full sm:w-[400px] z-50",
          "bg-[#fff6e9] border-l border-[#e0d4bf] shadow-2xl",
          "flex flex-col",
          "transform transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Chat with report"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#e0d4bf]">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-[#6b5344]" />
            <h2 className="text-base font-semibold text-[#4a3c2e]">Chat with Report</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#8b7355] hover:text-[#4a3c2e] transition-colors"
            aria-label="Close chat panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Messages */}
        <div ref={messagesContainerRef} className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="w-5 h-5 animate-spin text-[#8b7355]" />
            </div>
          )}

          {!isLoading && messages.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center h-full px-6 text-center">
              <MessageSquare className="w-10 h-10 text-[#e0d4bf] mb-4" />
              <h3 className="text-sm font-semibold text-[#6b5344] mb-1">Ask about this report</h3>
              <p className="text-xs text-[#8b7355] max-w-xs leading-relaxed">
                Ask questions about analysis results, claims, agent findings, IFRS compliance, or disclosure gaps.
              </p>
            </div>
          )}

          {error && (
            <div className="mx-4 mt-4 p-4 rounded-xl bg-rose-50 border border-rose-100">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-rose-700">{error}</p>
                  <button
                    onClick={clearError}
                    className="mt-1.5 text-xs text-rose-500 hover:text-rose-700 underline transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          )}

          {!isLoading && (
            <div className="divide-y divide-[#f0e8d8]">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} onCitationClick={handleCitationClick} />
              ))}
              {streamingMessage && (
                <ChatMessage message={streamingMessage} onCitationClick={handleCitationClick} isStreaming />
              )}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        {reportId ? (
          <ChatInput
            onSend={sendMessage}
            disabled={isStreaming || !reportId}
            placeholder={isStreaming ? "Waiting for response…" : "Ask about the report…"}
          />
        ) : (
          <div className="p-4 border-t border-[#e0d4bf]">
            <p className="text-xs text-center text-[#8b7355]">Select a report to start chatting</p>
          </div>
        )}
      </div>
    </>
  );
}
