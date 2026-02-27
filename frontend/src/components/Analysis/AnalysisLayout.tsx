/**
 * AnalysisLayout - Three-panel resizable layout for the Analysis page.
 * Implements FRD 4 Section 3 (Three-Panel Layout).
 *
 * Layout: PDF Viewer (left) | Dashboard (center) | Claims & Reasoning (right)
 */

import { useState, useCallback, useRef, useEffect, type ReactNode } from "react";

interface AnalysisLayoutProps {
  leftPanel: ReactNode;    // PDF Viewer
  centerPanel: ReactNode;  // Dashboard placeholder
  rightPanel: ReactNode;   // Claims & Reasoning
}

interface PanelWidths {
  left: number;
  center: number;
  right: number;
}

const MIN_PANEL_WIDTH = 250;
const DEFAULT_WIDTHS: PanelWidths = {
  left: 35,
  center: 40,
  right: 25,
};

export function AnalysisLayout({
  leftPanel,
  centerPanel,
  rightPanel,
}: AnalysisLayoutProps) {
  const [widths, setWidths] = useState<PanelWidths>(DEFAULT_WIDTHS);
  const containerRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef<"left" | "right" | null>(null);
  const startXRef = useRef<number>(0);
  const startWidthsRef = useRef<PanelWidths>(DEFAULT_WIDTHS);

  const handleMouseDown = useCallback(
    (handle: "left" | "right") => (e: React.MouseEvent) => {
      e.preventDefault();
      draggingRef.current = handle;
      startXRef.current = e.clientX;
      startWidthsRef.current = { ...widths };
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    },
    [widths]
  );

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!draggingRef.current || !containerRef.current) return;

      const containerWidth = containerRef.current.offsetWidth;
      const deltaX = e.clientX - startXRef.current;
      const deltaPercent = (deltaX / containerWidth) * 100;

      const minPercent = (MIN_PANEL_WIDTH / containerWidth) * 100;
      const startWidths = startWidthsRef.current;

      if (draggingRef.current === "left") {
        // Dragging between left and center
        let newLeft = startWidths.left + deltaPercent;
        let newCenter = startWidths.center - deltaPercent;

        // Enforce minimums
        if (newLeft < minPercent) {
          const diff = minPercent - newLeft;
          newLeft = minPercent;
          newCenter -= diff;
        }
        if (newCenter < minPercent) {
          const diff = minPercent - newCenter;
          newCenter = minPercent;
          newLeft -= diff;
        }

        setWidths({
          left: Math.max(minPercent, Math.min(newLeft, 100 - 2 * minPercent)),
          center: Math.max(minPercent, newCenter),
          right: startWidths.right,
        });
      } else {
        // Dragging between center and right
        let newCenter = startWidths.center + deltaPercent;
        let newRight = startWidths.right - deltaPercent;

        // Enforce minimums
        if (newCenter < minPercent) {
          const diff = minPercent - newCenter;
          newCenter = minPercent;
          newRight -= diff;
        }
        if (newRight < minPercent) {
          const diff = minPercent - newRight;
          newRight = minPercent;
          newCenter -= diff;
        }

        setWidths({
          left: startWidths.left,
          center: Math.max(minPercent, newCenter),
          right: Math.max(minPercent, Math.min(newRight, 100 - 2 * minPercent)),
        });
      }
    };

    const handleMouseUp = () => {
      if (draggingRef.current) {
        draggingRef.current = null;
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  return (
    <div className="analysis-layout" ref={containerRef}>
      {/* Left Panel - PDF Viewer */}
      <div
        className="analysis-layout__panel analysis-layout__panel--left"
        style={{ width: `${widths.left}%` }}
      >
        <div className="flex items-center px-4 py-2.5 border-b border-[#e0d4bf] bg-[#fff6e9]">
          <h3 className="text-xs font-semibold text-[#6b5344] uppercase tracking-wide">PDF Viewer</h3>
        </div>
        <div className="analysis-layout__panel-content">{leftPanel}</div>
      </div>

      {/* Resize Handle - Left/Center */}
      <div
        className="analysis-layout__resize-handle"
        onMouseDown={handleMouseDown("left")}
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize PDF viewer panel"
      />

      {/* Center Panel - Dashboard */}
      <div
        className="analysis-layout__panel analysis-layout__panel--center"
        style={{ width: `${widths.center}%` }}
      >
        <div className="flex items-center px-4 py-2.5 border-b border-[#e0d4bf] bg-[#fff6e9]">
          <h3 className="text-xs font-semibold text-[#6b5344] uppercase tracking-wide">Investigation</h3>
        </div>
        <div className="analysis-layout__panel-content">{centerPanel}</div>
      </div>

      {/* Resize Handle - Center/Right */}
      <div
        className="analysis-layout__resize-handle"
        onMouseDown={handleMouseDown("right")}
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize claims panel"
      />

      {/* Right Panel - Claims & Reasoning */}
      <div
        className="analysis-layout__panel analysis-layout__panel--right"
        style={{ width: `${widths.right}%` }}
      >
        <div className="flex items-center px-4 py-2.5 border-b border-[#e0d4bf] bg-[#fff6e9]">
          <h3 className="text-xs font-semibold text-[#6b5344] uppercase tracking-wide">Claims & Reasoning</h3>
        </div>
        <div className="analysis-layout__panel-content">{rightPanel}</div>
      </div>
    </div>
  );
}
