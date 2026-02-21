/**
 * ClaimEdge - Custom React Flow edge with particle animation.
 * Supports three edge types: claim, reinvestigation, infoRequest.
 */

import { memo } from "react";
import {
  BaseEdge,
  getBezierPath,
  EdgeLabelRenderer,
  type Position,
} from "@xyflow/react";
import type { ClaimEdgeData } from "@/types/dashboard";
import { ParticleAnimation } from "./ParticleAnimation";
import { getAgentHexColor, isAgentName } from "./layout";

interface ClaimEdgeProps {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition: Position;
  targetPosition: Position;
  data?: ClaimEdgeData;
  selected?: boolean;
  source: string;
}

function ClaimEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
  source,
}: ClaimEdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeType = data?.edgeType || "claim";
  const volume = data?.volume || "low";
  const label = data?.label;
  const cycleNumber = data?.cycleNumber;
  const sourceAgentColor = data?.sourceAgentColor;

  // Determine edge color based on type and source
  const defaultColor = isAgentName(source) ? getAgentHexColor(source) : "#94a3b8";
  let strokeColor = sourceAgentColor || defaultColor;
  let strokeDasharray: string | undefined;
  const strokeWidth = selected ? 3 : 2;

  if (edgeType === "reinvestigation") {
    strokeColor = getAgentHexColor("judge");
    strokeDasharray = "8,4";
  } else if (edgeType === "infoRequest") {
    strokeColor = getAgentHexColor("orchestrator");
    strokeDasharray = "4,4";
  }

  const edgeClassName = `claim-edge claim-edge--${edgeType} ${
    selected ? "claim-edge--selected" : ""
  }`;

  return (
    <>
      {/* Base edge path */}
      <BaseEdge
        id={id}
        path={edgePath}
        className={edgeClassName}
        style={{
          stroke: strokeColor,
          strokeWidth,
          strokeDasharray,
        }}
      />

      {/* Particle animation */}
      <ParticleAnimation
        edgePath={edgePath}
        volume={volume}
        color={strokeColor}
        direction={data?.direction || "forward"}
      />

      {/* Edge label */}
      {(label || cycleNumber) && (
        <EdgeLabelRenderer>
          <div
            className="claim-edge__label"
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
          >
            {cycleNumber && (
              <span className="claim-edge__cycle-badge">Cycle {cycleNumber}</span>
            )}
            {label && <span className="claim-edge__text">{label}</span>}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const ClaimEdge = memo(ClaimEdgeComponent);
