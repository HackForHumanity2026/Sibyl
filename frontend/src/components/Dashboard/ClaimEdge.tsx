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
  EdgeLabelRenderer,
  type Position,
} from "@xyflow/react";
import type { ClaimEdgeData } from "@/types/dashboard";
import { ParticleAnimation } from "./ParticleAnimation";
import { getAgentHexColor, isAgentName } from "./layout";

const SPECIALIST_AGENTS = new Set([
  "geography",
  "legal",
  "news_media",
  "academic",
  "data_metrics",
]);

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
  target: string;
}

interface Point {
  x: number;
  y: number;
}

const AGENT_BORDER_RADIUS = 48;

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
  const swoopY = Math.max(sourceY, targetY) + 210;
  const control1X = sourceX + 60;
  const control2X = targetX - 60;
  const path = `M ${sourceX},${sourceY} C ${control1X},${swoopY} ${control2X},${swoopY} ${targetX},${targetY}`;

  const [labelX, labelY] = cubicPoint(
    { x: sourceX, y: sourceY },
    { x: control1X, y: swoopY },
    { x: control2X, y: swoopY },
    { x: targetX, y: targetY },
    0.5
  );

  return [path, labelX, labelY];
}

function anchorToBorders(source: Point, target: Point, radius = AGENT_BORDER_RADIUS): [Point, Point] {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const dist = Math.hypot(dx, dy);

  if (dist < 0.001) {
    return [source, target];
  }

  const ux = dx / dist;
  const uy = dy / dist;

  return [
    { x: source.x + ux * radius, y: source.y + uy * radius },
    { x: target.x - ux * radius, y: target.y - uy * radius },
  ];
}

function quadraticPoint(p0: Point, p1: Point, p2: Point, t: number): [number, number] {
  const mt = 1 - t;
  const x = mt * mt * p0.x + 2 * mt * t * p1.x + t * t * p2.x;
  const y = mt * mt * p0.y + 2 * mt * t * p1.y + t * t * p2.y;
  return [x, y];
}

function cubicPoint(p0: Point, p1: Point, p2: Point, p3: Point, t: number): [number, number] {
  const mt = 1 - t;
  const mt2 = mt * mt;
  const t2 = t * t;
  const x = mt2 * mt * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t2 * t * p3.x;
  const y = mt2 * mt * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t2 * t * p3.y;
  return [x, y];
}

function buildCurvedPath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  bend: number
): [string, number, number] {
  const p0 = { x: sourceX, y: sourceY };
  const p2 = { x: targetX, y: targetY };
  const mx = (p0.x + p2.x) / 2;
  const my = (p0.y + p2.y) / 2;

  const dx = p2.x - p0.x;
  const dy = p2.y - p0.y;
  const dist = Math.hypot(dx, dy) || 1;
  const nx = -dy / dist;
  const ny = dx / dist;

  const p1 = {
    x: mx + nx * bend,
    y: my + ny * bend,
  };

  const path = `M ${p0.x},${p0.y} Q ${p1.x},${p1.y} ${p2.x},${p2.y}`;
  const [labelX, labelY] = quadraticPoint(p0, p1, p2, 0.5);
  return [path, labelX, labelY];
}

interface InteractionPoints {
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
}

interface InteractionPositions {
  sourcePosition: Position;
  targetPosition: Position;
}

function buildInteractionPath(
  edgeType: ClaimEdgeData["edgeType"],
  source: string,
  target: string,
  points: InteractionPoints,
  positions: InteractionPositions
): [string, number, number] {
  const { sourceX, sourceY, targetX, targetY } = points;
  const { sourcePosition, targetPosition } = positions;

  // React Flow already provides handle coordinates at node borders —
  // use them directly without further projection.
  const sx = sourceX;
  const sy = sourceY;
  const tx = targetX;
  const ty = targetY;

  if (edgeType === "reinvestigation") {
    return buildSwoopPath(sx, sy, tx, ty);
  }

  if (source === "orchestrator" && SPECIALIST_AGENTS.has(target)) {
    // Scale bend by distance so far targets arc wide around intermediate nodes
    const dist = Math.hypot(tx - sx, ty - sy);
    const bendMag = Math.max(90, dist * 0.38);
    const isUpper = target === "legal" || target === "geography" || target === "news_media";
    return buildCurvedPath(sx, sy, tx, ty, isUpper ? -bendMag : bendMag);
  }

  if (SPECIALIST_AGENTS.has(source) && target === "judge") {
    const dist = Math.hypot(tx - sx, ty - sy);
    const bendMag = Math.max(80, dist * 0.32);
    const isUpper = source === "legal" || source === "geography" || source === "news_media";
    return buildCurvedPath(sx, sy, tx, ty, isUpper ? -bendMag : bendMag);
  }

  if (SPECIALIST_AGENTS.has(source) && target === "orchestrator") {
    const dist = Math.hypot(tx - sx, ty - sy);
    const bendMag = Math.max(80, dist * 0.32);
    const isUpper = source === "legal" || source === "geography" || source === "news_media";
    return buildCurvedPath(sx, sy, tx, ty, isUpper ? -bendMag : bendMag);
  }

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX: sx,
    sourceY: sy,
    sourcePosition,
    targetX: tx,
    targetY: ty,
    targetPosition,
    curvature: 0.28,
  });
  return [edgePath, labelX, labelY];
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
  target,
}: Readonly<ClaimEdgeProps>) {
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

  // Use layout-aware curved paths to avoid clipping through avatars and preserve
  // intuitive directional flow for common interaction pairs.
  let edgePath: string;
  let labelX: number;
  let labelY: number;
  [edgePath, labelX, labelY] = buildInteractionPath(
    edgeType,
    source,
    target,
    {
      sourceX,
      sourceY,
      targetX,
      targetY,
    },
    {
      sourcePosition,
      targetPosition,
    }
  );

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
