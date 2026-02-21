/**
 * EdgePopover - Popover showing edge details when clicked.
 * Displays claim/evidence data, reinvestigation info, or InfoRequest details.
 */

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Edge } from "@xyflow/react";
import type { ClaimEdgeData } from "@/types/dashboard";
import { getAgentDisplayName, isAgentName } from "./layout";

interface EdgePopoverProps {
  edge: Edge<ClaimEdgeData> | null;
  position: { x: number; y: number };
  onClose: () => void;
}

export function EdgePopover({ edge, position, onClose }: EdgePopoverProps) {
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close on click outside or Escape
  useEffect(() => {
    if (!edge) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as globalThis.Node)
      ) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [edge, onClose]);

  if (!edge) return null;

  const { source, target, data } = edge;
  const edgeType = data?.edgeType;
  const cycleNumber = data?.cycleNumber;
  const messages = data?.messages;
  const label = data?.label;

  const sourceDisplayName = isAgentName(source)
    ? getAgentDisplayName(source)
    : source;
  const targetDisplayName = isAgentName(target)
    ? getAgentDisplayName(target)
    : target;

  return (
    <AnimatePresence>
      <motion.div
        ref={popoverRef}
        className="edge-popover"
        style={{
          position: "absolute",
          left: position.x,
          top: position.y,
          transform: "translate(-50%, -100%)",
          zIndex: 1000,
        }}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 10 }}
        transition={{ duration: 0.15 }}
      >
        <div className="edge-popover__header">
          <span className="edge-popover__route">
            {sourceDisplayName} → {targetDisplayName}
          </span>
          <button
            className="edge-popover__close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="edge-popover__content">
          {edgeType === "claim" && (
            <div className="edge-popover__section">
              <div className="edge-popover__section-title">Claim Routing</div>
              {messages && messages.length > 0 ? (
                <div className="edge-popover__messages">
                  {messages.slice(-3).map((msg) => (
                    <div key={msg.id} className="edge-popover__message">
                      {msg.claimText && (
                        <div className="edge-popover__claim-text">
                          {msg.claimText.slice(0, 100)}
                          {msg.claimText.length > 100 ? "..." : ""}
                        </div>
                      )}
                      <div className="edge-popover__timestamp">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="edge-popover__empty">
                  Claims routed from {sourceDisplayName} to {targetDisplayName}
                </div>
              )}
            </div>
          )}

          {edgeType === "reinvestigation" && (
            <div className="edge-popover__section">
              <div className="edge-popover__section-title">
                Re-investigation Request
              </div>
              {cycleNumber && (
                <div className="edge-popover__cycle">
                  <span className="edge-popover__cycle-badge">
                    Cycle {cycleNumber}
                  </span>
                </div>
              )}
              {messages && messages[0]?.requestDescription && (
                <div className="edge-popover__description">
                  {messages[0].requestDescription}
                </div>
              )}
            </div>
          )}

          {edgeType === "infoRequest" && (
            <div className="edge-popover__section">
              <div className="edge-popover__section-title">
                Inter-Agent Communication
              </div>
              {label && (
                <div className="edge-popover__label">{label}</div>
              )}
              {messages && messages.length > 0 && (
                <div className="edge-popover__messages">
                  {messages.map((msg) => (
                    <div key={msg.id} className="edge-popover__message">
                      {msg.requestDescription && (
                        <div className="edge-popover__request">
                          Request: {msg.requestDescription}
                        </div>
                      )}
                      {msg.responseText && (
                        <div className="edge-popover__response">
                          Response: {msg.responseText.slice(0, 100)}...
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
