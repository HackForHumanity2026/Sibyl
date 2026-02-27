/**
 * ClaimEdge - Custom React Flow edge with particle animation.
 * Supports three edge types: claim, reinvestigation, infoRequest.
 *
 * Reinvestigation edges use a custom swooping path that dips below
 * the specialist area instead of cutting through it.
 */

import { memo } from "react";
import {
  BaseEdge,
  getBezierPath,
  getStraightPath,
  EdgeLabelRenderer,
  type Position,
} from "@xyflow/react";
import type { ClaimEdgeData } from "@/types/dashboard";
import { ParticleAnimation } from "./ParticleAnimation";
import { getAgentHexColor, isAgentName } from "./layout";

// The Y position to swoop down to (below all specialist nodes)
// Pentagon layout: centreY=350, radius=200 → lowest specialist ~550
// Swoop to 750 to be safely below the message pool node and all specialists
const REINVESTIGATION_SWOOP_Y = 750;

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

/**
 * Builds a custom SVG path for reinvestigation edges that swoops below
 * the specialist area. Path: source → dip below → target.
 */
function buildSwoopPath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number
): [string, number, number] {
  const swoopY = REINVESTIGATION_SWOOP_Y;
  const midX = (sourceX + targetX) / 2;

  // Cubic bezier: exits source bottom, sweeps below all agents, enters target bottom
  const path = `M ${sourceX},${sourceY} C ${sourceX},${swoopY} ${targetX},${swoopY} ${targetX},${targetY}`;

  // Label at the midpoint of the swoop
  const labelX = midX;
  const labelY = swoopY + 20;

  return [path, labelX, labelY];
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
  const edgeType = data?.edgeType || "claim";
  const volume = data?.volume || "low";
  const label = data?.label;
  const cycleNumber = data?.cycleNumber;
  const sourceAgentColor = data?.sourceAgentColor;

  // Determine edge color based on type and source
  const defaultColor = isAgentName(source) ? getAgentHexColor(source) : "#94a3b8";
  let strokeColor = sourceAgentColor || defaultColor;
  let strokeDasharray: string | undefined;
  // Thinner lines, slightly transparent to reduce visual noise when many edges overlap
  const strokeWidth = selected ? 2 : 1.5;
  const strokeOpacity = selected ? 1 : 0.65;

  if (edgeType === "reinvestigation") {
    strokeColor = getAgentHexColor("judge");
    strokeDasharray = "8,4";
  } else if (edgeType === "infoRequest") {
    strokeColor = getAgentHexColor("orchestrator");
    strokeDasharray = "4,4";
  }

  // Use custom swoop path for reinvestigation edges,
  // straight paths for claim/infoRequest (cleaner hub-and-spoke star),
  // bezier for any other edge type.
  let edgePath: string;
  let labelX: number;
  let labelY: number;

  if (edgeType === "reinvestigation") {
    // Attach from bottom of source (judge), swoop down, attach to bottom of target (orchestrator)
    [edgePath, labelX, labelY] = buildSwoopPath(
      sourceX,
      sourceY + 50,   // exit bottom of judge node
      targetX,
      targetY + 50    // enter bottom of orchestrator node
    );
  } else if (edgeType === "claim" || edgeType === "infoRequest") {
    // Straight lines look cleaner in a star/pentagon hub pattern
    [edgePath, labelX, labelY] = getStraightPath({ sourceX, sourceY, targetX, targetY });
  } else {
    [edgePath, labelX, labelY] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
    });
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
          strokeOpacity,
        }}
      />

      {/* Particle animation (only for non-reinvestigation edges to avoid visual noise) */}
      {edgeType !== "reinvestigation" && (
        <ParticleAnimation
          edgePath={edgePath}
          volume={volume}
          color={strokeColor}
          direction={data?.direction || "forward"}
        />
      )}

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
