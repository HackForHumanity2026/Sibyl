/**
 * MessagePoolNode — a purely visual, non-interactive React Flow node
 * rendered as a semi-transparent table at the center of the specialist
 * pentagon. It shows the last few info_request / info_response events
 * scrolling through.
 */

import { memo, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { StreamEvent } from "@/services/sse";

interface MessagePoolNodeProps {
  data: {
    events: StreamEvent[];
  };
}

interface PoolMessage {
  id: string;
  kind: "request" | "response";
  text: string;
}

function MessagePoolNodeComponent({ data }: MessagePoolNodeProps) {
  const messages: PoolMessage[] = useMemo(() => {
    const filtered = data.events.filter(
      (e) =>
        e.event_type === "info_request_routed" ||
        e.event_type === "info_response_posted"
    );
    return filtered
      .slice(-4)
      .reverse()
      .map((e) => {
        const kind =
          e.event_type === "info_request_routed" ? "request" : "response";
        let text = "";
        if (kind === "request") {
          const desc = (e.data as { description?: string })?.description ?? "";
          const from =
            (e.data as { requesting_agent?: string })?.requesting_agent ??
            e.agent_name;
          text = `${from}: ${desc}`.slice(0, 60);
        } else {
          const resp =
            (e.data as { response?: string })?.response ??
            (e.data as { content?: string })?.content ??
            "";
          text = `${e.agent_name}: ${resp}`.slice(0, 60);
        }
        return { id: `${e.event_type}-${e.timestamp}`, kind, text };
      });
  }, [data.events]);

  return (
    // pointer-events: none so this node doesn't block edge interaction
    <div className="message-pool-node" style={{ pointerEvents: "none" }}>
      <p className="message-pool-node__label">Message Pool</p>
      <div className="message-pool-node__body">
        <AnimatePresence initial={false}>
          {messages.length === 0 ? (
            <motion.p
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              className="message-pool-node__idle"
            >
              Awaiting messages…
            </motion.p>
          ) : (
            messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.25 }}
                className="message-pool-node__row"
              >
                <span
                  className={`message-pool-node__badge ${
                    msg.kind === "request"
                      ? "message-pool-node__badge--req"
                      : "message-pool-node__badge--res"
                  }`}
                >
                  {msg.kind === "request" ? "Req" : "Res"}
                </span>
                <span className="message-pool-node__text">{msg.text}</span>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export const MessagePoolNode = memo(MessagePoolNodeComponent);
