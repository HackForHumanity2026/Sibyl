/**
 * ReasoningStream - Scrollable list of recent agent reasoning messages.
 */

import { useEffect, useRef } from "react";

interface ReasoningStreamProps {
  messages: string[];
  maxMessages?: number;
}

export function ReasoningStream({
  messages,
  maxMessages = 10,
}: ReasoningStreamProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const displayMessages = messages.slice(-maxMessages);

  if (displayMessages.length === 0) {
    return (
      <div className="reasoning-stream reasoning-stream--empty">
        <span className="reasoning-stream__placeholder">
          Waiting for agent activity...
        </span>
      </div>
    );
  }

  return (
    <div className="reasoning-stream" ref={scrollRef}>
      <div className="reasoning-stream__header">Reasoning</div>
      <div className="reasoning-stream__messages">
        {displayMessages.map((message, index) => (
          <div key={`${index}-${message.slice(0, 20)}`} className="reasoning-stream__message">
            <span className="reasoning-stream__bullet">•</span>
            <span className="reasoning-stream__text">{message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
