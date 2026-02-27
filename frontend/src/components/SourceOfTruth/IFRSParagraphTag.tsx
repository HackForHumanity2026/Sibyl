/**
 * IFRSParagraphTag - Badge for IFRS paragraph identifiers with hover tooltip.
 * Shows the full requirement_text from the bundled paragraph registry on hover.
 * Implements FRD 13 Section 6.4.
 */

import { useState, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { getParagraphInfo } from "@/data/paragraphRegistry";

interface IFRSParagraphTagProps {
  paragraphId: string;
  relevance?: string | null;
}

export function IFRSParagraphTag({ paragraphId, relevance }: IFRSParagraphTagProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const info = getParagraphInfo(paragraphId);
  const MAX_TEXT = 180;
  const requirementText = info?.requirement_text ?? relevance ?? null;
  const isTruncated = requirementText && requirementText.length > MAX_TEXT;
  const displayText = isTruncated && !expanded
    ? requirementText!.slice(0, MAX_TEXT) + "…"
    : requirementText;

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setIsHovered(false);
      setExpanded(false);
    }, 120);
  };

  return (
    <span
      className="ifrs-tag-wrapper"
      style={{ position: "relative", display: "inline-flex" }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono bg-[#eddfc8] text-[#4a3c2e] font-semibold cursor-default select-none">
        {paragraphId}
      </span>

      <AnimatePresence>
        {isHovered && (info || relevance) && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.97 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            style={{
              position: "absolute",
              bottom: "calc(100% + 6px)",
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 9999,
              width: "260px",
              pointerEvents: "auto",
            }}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <div
              style={{
                background: "#fff6e9",
                border: "1px solid #e0d4bf",
                borderRadius: "8px",
                boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
                padding: "10px 12px",
              }}
            >
              {/* Header */}
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                <span
                  style={{
                    fontFamily: "monospace",
                    fontSize: "11px",
                    fontWeight: 700,
                    background: "#eddfc8",
                    color: "#4a3c2e",
                    padding: "1px 6px",
                    borderRadius: "4px",
                  }}
                >
                  {paragraphId}
                </span>
                {info && (
                  <span style={{ fontSize: "10px", color: "#8b7355", fontWeight: 500 }}>
                    {info.standard} · {info.section}
                  </span>
                )}
              </div>

              {/* Requirement text */}
              {displayText && (
                <p style={{ fontSize: "11px", color: "#4a3c2e", lineHeight: 1.5, margin: 0 }}>
                  {displayText}
                  {isTruncated && !expanded && (
                    <button
                      onClick={(e) => { e.stopPropagation(); setExpanded(true); }}
                      style={{
                        marginLeft: "4px",
                        color: "#d97706",
                        background: "none",
                        border: "none",
                        padding: 0,
                        fontSize: "11px",
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                    >
                      more
                    </button>
                  )}
                </p>
              )}

              {/* Arrow pointing down */}
              <div
                style={{
                  position: "absolute",
                  bottom: "-5px",
                  left: "50%",
                  transform: "translateX(-50%)",
                  width: 0,
                  height: 0,
                  borderLeft: "5px solid transparent",
                  borderRight: "5px solid transparent",
                  borderTop: "5px solid #e0d4bf",
                }}
              />
              <div
                style={{
                  position: "absolute",
                  bottom: "-4px",
                  left: "50%",
                  transform: "translateX(-50%)",
                  width: 0,
                  height: 0,
                  borderLeft: "4px solid transparent",
                  borderRight: "4px solid transparent",
                  borderTop: "4px solid #fff6e9",
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
}
