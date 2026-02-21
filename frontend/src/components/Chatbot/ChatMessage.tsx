/**
 * ChatMessage component - Individual message bubble.
 * Implements FRD 14 (Chatbot) Section 9 - Chat Message Component.
 */

import { useMemo } from "react";
import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType, Citation } from "@/types/chat";

interface ChatMessageProps {
  message: ChatMessageType;
  onCitationClick?: (citation: Citation) => void;
  isStreaming?: boolean;
}

/**
 * Parse message content and render inline citations as clickable badges.
 */
function renderContentWithCitations(
  content: string,
  citations: Citation[],
  onCitationClick?: (citation: Citation) => void
): React.ReactNode[] {
  // Create a map of citation numbers to citations
  const citationMap = new Map<number, Citation>();
  for (const citation of citations) {
    citationMap.set(citation.citation_number, citation);
  }

  // Split content by citation markers [N]
  const parts: React.ReactNode[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    // Add text before the citation
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }

    const citationNum = Number.parseInt(match[1], 10);
    const citation = citationMap.get(citationNum);

    if (citation && onCitationClick) {
      // Render as clickable badge
      parts.push(
        <button
          key={`citation-${match.index}`}
          onClick={() => onCitationClick(citation)}
          className="inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1.5 mx-0.5 
                     text-xs font-medium rounded-full
                     bg-blue-100 text-blue-700 hover:bg-blue-200
                     dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800
                     transition-colors cursor-pointer"
          title={citation.display_text}
        >
          {citationNum}
        </button>
      );
    } else {
      // Render as plain text if no citation found or no click handler
      parts.push(`[${citationNum}]`);
    }

    lastIndex = regex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return parts;
}

export function ChatMessage({
  message,
  onCitationClick,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  const renderedContent = useMemo(() => {
    if (isUser || message.citations.length === 0) {
      return message.content;
    }
    return renderContentWithCitations(
      message.content,
      message.citations,
      onCitationClick
    );
  }, [message.content, message.citations, isUser, onCitationClick]);

  return (
    <div
      className={cn(
        "flex gap-3 p-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </div>

      {/* Message bubble */}
      <div
        className={cn(
          "flex flex-col max-w-[80%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5",
            isUser
              ? "bg-blue-600 text-white rounded-br-md"
              : "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100 rounded-bl-md"
          )}
        >
          <div className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            {renderedContent}
            {isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse rounded-sm" />
            )}
          </div>
        </div>

        {/* Citations summary for assistant messages */}
        {!isUser && message.citations.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {message.citations.map((citation) => (
              <button
                key={citation.citation_number}
                onClick={() => onCitationClick?.(citation)}
                className="text-xs px-2 py-0.5 rounded-full
                           bg-gray-200 text-gray-600 hover:bg-gray-300
                           dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600
                           transition-colors cursor-pointer"
                title={`Navigate to ${citation.display_text}`}
              >
                [{citation.citation_number}] {citation.display_text}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
