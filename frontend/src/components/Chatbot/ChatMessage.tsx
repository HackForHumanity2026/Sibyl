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

function renderContentWithCitations(
  content: string,
  citations: Citation[],
  onCitationClick?: (citation: Citation) => void
): React.ReactNode[] {
  const citationMap = new Map<number, Citation>();
  for (const citation of citations) citationMap.set(citation.citation_number, citation);

  const parts: React.ReactNode[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) parts.push(content.slice(lastIndex, match.index));

    const citationNum = Number.parseInt(match[1], 10);
    const citation    = citationMap.get(citationNum);

    if (citation && onCitationClick) {
      parts.push(
        <button
          key={`citation-${match.index}`}
          onClick={() => onCitationClick(citation)}
          className="inline-flex items-center justify-center min-w-[1.25rem] h-4 px-1 mx-0.5
                     text-xs font-semibold rounded-full
                     bg-[#eddfc8] text-[#4a3c2e] hover:bg-[#e4d3ba]
                     transition-colors cursor-pointer"
          title={citation.display_text}
        >
          {citationNum}
        </button>
      );
    } else {
      parts.push(`[${citationNum}]`);
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < content.length) parts.push(content.slice(lastIndex));
  return parts;
}

export function ChatMessage({ message, onCitationClick, isStreaming = false }: ChatMessageProps) {
  const isUser = message.role === "user";

  const renderedContent = useMemo(() => {
    if (isUser || message.citations.length === 0) return message.content;
    return renderContentWithCitations(message.content, message.citations, onCitationClick);
  }, [message.content, message.citations, isUser, onCitationClick]);

  return (
    <div className={cn("flex gap-3 px-4 py-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div className={cn(
        "shrink-0 w-7 h-7 rounded-full flex items-center justify-center",
        isUser ? "bg-[#4a3c2e] text-white" : "bg-[#eddfc8] text-[#6b5344]"
      )}>
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Message content */}
      <div className={cn("flex flex-col max-w-[80%]", isUser ? "items-end" : "items-start")}>
        <div className={cn(
          isUser
            ? "rounded-2xl rounded-br-md px-3.5 py-2.5 bg-[#4a3c2e] text-white"
            : "text-[#4a3c2e] py-1"
        )}>
          <div className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            {renderedContent}
            {isStreaming && (
              <span className="inline-block w-1.5 h-3.5 ml-1 bg-current animate-pulse rounded-sm" />
            )}
          </div>
        </div>

        {/* Citation chips */}
        {!isUser && message.citations.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {message.citations.map((citation) => (
              <button
                key={citation.citation_number}
                onClick={() => onCitationClick?.(citation)}
                className="text-xs px-2 py-0.5 rounded-full bg-[#eddfc8] text-[#6b5344] hover:bg-[#e4d3ba] transition-colors"
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
