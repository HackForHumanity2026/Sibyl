# Feature Requirements Document: FRD 12 -- Detective Dashboard (v2.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.4](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.10 (Detective Dashboard), 7.2 (Analysis Page) |
| **Type** | Feature |
| **Depends On** | FRD 5 (Orchestrator Agent & LangGraph Pipeline), FRDs 6-11 (all specialist agents + Judge) |
| **Delivers** | Real-time React Flow "avatar village" graph; egg-shaped avatar nodes; Message Pool in-graph table; horizontal pentagon layout; bottom-sheet detail view; AgentNavBar; VillageBackground; module-level event and graph-state caches; confetti on completion; reinvestigation swoop-under edge |
| **Created** | 2026-02-09 |
| **Revised** | 2026-02-27 (v2.0 -- complete rewrite to match implemented design) |

---

## Summary

FRD 12 delivers the Detective Dashboard -- the hero visual of Sibyl. The implementation diverges significantly from the v1.0 specification: rather than dark rectangular blocks in a vertical pipeline, the dashboard renders a warm-cream "detective village" where every agent is an animated, egg-shaped avatar character. The five specialist agents are arranged in a pentagon around a central Message Pool table, with the Claims agent near the Orchestrator on the left and the Judge on the right, creating a natural left-to-right reading of the investigation flow. Clicking an avatar opens a bottom sheet that slides up from beneath the navigator bar, showing the agent's full reasoning history, findings, and agent-specific content. The graph, navigator bar, bottom sheet, and background village elements are all managed within a single React Flow canvas inside `DashboardGraph.tsx`.

---

## Given Context (Preconditions)

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| LangGraph StateGraph with all nodes | FRD 5, FRDs 6-11 | `app/agents/graph.py` |
| SSE streaming infrastructure with `StreamEvent` | FRD 5 | `app/api/routes/stream.py` |
| `useSSE` hook | FRD 5 | `src/hooks/useSSE.ts` |
| `StreamEvent` TypeScript types | FRD 5 | `src/services/sse.ts` |
| Analysis Page split-panel layout | FRD 4 | `src/pages/AnalysisPage.tsx` |
| `AgentVillage.tsx` with exported `EggAvatar`, `AGENTS`, `AgentMark` | FRD 12 (this) | `src/components/AgentVillage.tsx` |
| `AgentName` union type (includes `"judge"`, `"message_pool"`) | FRD 0 | `src/types/agent.ts` |
| `@xyflow/react` installed | FRD 0 | `package.json` |
| `canvas-confetti` installed | FRD 12 | `package.json` |
| `framer-motion` installed | FRD 0 | `package.json` |

### Terms

| Term | Definition |
|---|---|
| EggAvatar | The egg-shaped SVG avatar component from `AgentVillage.tsx`, used as the visual identity for each agent |
| EggAvatarNode | Custom React Flow node that wraps `EggAvatar` and shows the agent's most recent pulsating reasoning text below it |
| MessagePoolNode | Custom React Flow node rendering a semi-transparent table of recent InfoRequest/InfoResponse messages |
| AgentDetailSheet | Bottom sheet component that slides up from beneath the AgentNavBar when an avatar is clicked, showing the agent's full detail view |
| AgentNavBar | Fixed navigator bar at the bottom of the graph canvas showing all agent avatars as small clickable icons |
| VillageBackground | SVG decorative layer (huts, trees, path) rendered at very low opacity behind the graph canvas |
| Pentagon layout | The spatial arrangement of the five specialist agents (Geography, Legal, News/Media, Academic, Data/Metrics) at pentagon vertices around the central Message Pool node |
| Module-level cache | A JavaScript `Map` stored at module scope (outside any React component) that persists data across component unmounts/remounts, used for SSE events and graph state |
| Swoop-under edge | The custom quadratic-bezier path for the reinvestigation edge that arcs wide below all specialist agents to avoid visual clutter |
| Warm cream theme | The global design system using `#fff6e9` background, warm brown text, and zero cold greys |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Detective Dashboard -- Avatar Village Visualization

  Background:
    Given  a sustainability report has been uploaded
    And    the user navigates to /analysis/{reportId}
    And    the Analysis Page loads with the Investigation tab active

  Scenario: Render the avatar village graph
    When   the graph canvas loads
    Then   egg-shaped avatar nodes appear for all agents
    And    the five specialist agents are arranged in a pentagon
    And    the Message Pool table occupies the center of the pentagon
    And    the Claims agent is positioned near the Orchestrator on the left
    And    the Judge agent is positioned on the far right
    And    village decorative elements (huts, trees) appear at low opacity behind the canvas

  Scenario: Display pulsating reasoning under each avatar
    Given  the pipeline is executing
    When   an agent emits a reasoning event
    Then   the most recent reasoning message appears below the agent's avatar
    And    the text pulses gently while the agent is active
    And    when the pipeline completes, the pulsating stops

  Scenario: Click an avatar to open the bottom sheet
    Given  the avatar village is rendered
    When   the user clicks on any avatar node
    Then   the AgentDetailSheet slides up from beneath the AgentNavBar
    And    the sheet shows the agent's name, role, and status
    And    the sheet shows the full historical reasoning stream
    And    the sheet shows findings and agent-specific content
    And    the AgentNavBar remains visible above the sheet

  Scenario: Click an avatar in the navigator bar
    Given  the AgentNavBar is visible at the bottom of the canvas
    When   the user clicks a small avatar icon in the bar
    Then   the same AgentDetailSheet opens for that agent

  Scenario: Visualize the Message Pool
    Given  the pipeline is executing
    When   InfoRequest or InfoResponse events arrive
    Then   the Message Pool table node in the center of the pentagon updates
    And    recent messages are displayed in table rows
    And    agent avatar nodes render visually on top of the table

  Scenario: Animate edges between agents
    Given  claims are being routed
    When   the graph updates
    Then   straight lines in the source agent's color connect agents for claim and infoRequest flows
    And    particle animations travel along the edge path
    And    the reinvestigation edge from Judge to Orchestrator arcs widely beneath the specialist cluster

  Scenario: Complete the pipeline with confetti
    Given  the pipeline is running
    When   a pipeline_completed event is received
    Then   confetti fires from both sides of the screen
    And    all reasoning streams stop pulsating
    And    all agent statuses update to 'completed'

  Scenario: Persist state across navigation
    Given  an analysis has been viewed
    When   the user navigates away and returns
    Then   all SSE events are restored from the module-level event cache
    And    the graph state is restored from the module-level graph state cache
    And    the full reasoning history is visible in the bottom sheet
```

---

## Table of Contents

1. [Component Architecture](#1-component-architecture)
2. [Graph Layout and Node Positioning](#2-graph-layout-and-node-positioning)
3. [EggAvatarNode Component](#3-eggavatarnode-component)
4. [MessagePoolNode Component](#4-messagepoolnode-component)
5. [VillageBackground Component](#5-villagebackground-component)
6. [Custom ClaimEdge Component](#6-custom-claimedge-component)
7. [AgentDetailSheet Component](#7-agentdetailsheet-component)
8. [AgentNavBar Component](#8-agentnavbar-component)
9. [SSE Event Processing and State (useDashboard)](#9-sse-event-processing-and-state-usedashboard)
10. [State Persistence (Module-Level Caches)](#10-state-persistence-module-level-caches)
11. [Confetti and Completion](#11-confetti-and-completion)
12. [Analysis Page Integration](#12-analysis-page-integration)
13. [Animation System](#13-animation-system)
14. [Design System Compliance](#14-design-system-compliance)
15. [Error and Edge Case Handling](#15-error-and-edge-case-handling)
16. [Exit Criteria](#16-exit-criteria)
17. [Appendix A: Agent Roster](#appendix-a-agent-roster)
18. [Appendix B: Graph Layout Coordinates](#appendix-b-graph-layout-coordinates)
19. [Appendix C: SSE Event to Graph Update Mapping](#appendix-c-sse-event-to-graph-update-mapping)
20. [Design Decisions Log](#design-decisions-log)

---

## 1. Component Architecture

### 1.1 File Structure

```
src/components/
  AgentVillage.tsx          # Source of truth for agent definitions (AGENTS, EggAvatar,
                            # AgentMark); exports reused by both landing page and Dashboard
  Dashboard/
    DashboardGraph.tsx      # Main component; ReactFlowProvider wrapper, DashboardGraphInner,
                            # AgentNavBar, AgentDetailSheet, confetti trigger
    DashboardGraph.css      # All styles for graph, avatar nodes, bottom sheet, nav bar
    EggAvatarNode.tsx       # Custom React Flow node: EggAvatar + pulsating reasoning text
    MessagePoolNode.tsx     # Custom React Flow node: semi-transparent message pool table
    ClaimEdge.tsx           # Custom React Flow edge: straight (claim/infoRequest),
                            # swoop-under bezier (reinvestigation)
    AgentDetailSheet.tsx    # Bottom sheet: tabbed reasoning/findings/agent content
    VillageBackground.tsx   # Decorative SVG overlay at <12% opacity
    layout.ts               # AGENT_POSITIONS, ALL_AGENTS, AGENT_DISPLAY_NAMES,
                            # AGENT_HEX_COLORS, LAYOUT_CONFIG
src/hooks/
  useDashboard.ts           # Processes SSE events → React Flow nodes + edges;
                            # module-level graphStateCache keyed by reportId
  useSSE.ts                 # SSE connection; module-level eventCache keyed by reportId
```

### 1.2 DashboardGraph Component

`DashboardGraph.tsx` exports a single default component that wraps the entire graph in `ReactFlowProvider`. The inner `DashboardGraphInner` component has access to the React Flow instance and calls `fitView()` programmatically when nodes first populate.

```typescript
// Simplified structure
const nodeTypes = {
  eggAvatar: EggAvatarNode,
  messagePool: MessagePoolNode,
};

const edgeTypes = {
  claim: ClaimEdge,
  reinvestigation: ClaimEdge,
  infoRequest: ClaimEdge,
};

function DashboardGraphInner({ reportId, onAgentSelect }) {
  const { nodes, edges } = useDashboard(reportId);
  const { fitView } = useReactFlow();

  // Fit view on first node population
  useEffect(() => {
    if (nodes.length > 0) {
      fitView({ padding: 0.04, duration: 600 });
    }
  }, [nodes.length > 0]);

  return (
    <>
      <VillageBackground />
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        nodesDraggable={false}
        fitView
        paddingBottom={80}  // Reserve space for AgentNavBar
      >
        <Controls />
      </ReactFlow>
      <AgentNavBar onSelect={onAgentSelect} />
      <AgentDetailSheet selectedAgentId={selectedAgentId} onClose={...} />
    </>
  );
}
```

### 1.3 React Flow Configuration

| Setting | Value | Rationale |
|---|---|---|
| `nodesDraggable` | `false` | Positions are static; dragging is not useful for a fixed village layout |
| `fitView` | `true` | Initial fit; then overridden by programmatic `fitView()` on node load |
| `fitViewOptions.padding` | `0.04` | Minimal padding to maximize canvas use |
| `paddingBottom` | `80` | Prevents bottom nodes from being hidden behind AgentNavBar |
| `nodeTypes` | `{ eggAvatar, messagePool }` | Custom node components only; no default nodes |
| `edgeTypes` | `{ claim, reinvestigation, infoRequest }` | Single `ClaimEdge` component handles all edge types with different styling |
| `proOptions.hideAttribution` | `true` | Clean canvas; no React Flow watermark |

---

## 2. Graph Layout and Node Positioning

### 2.1 Orientation

The graph uses a **horizontal left-to-right** orientation:

- **Claims agent (Menny):** Far left, positioned close to the Orchestrator
- **Orchestrator (Bron):** Left of center
- **Specialist pentagon:** Center; five agents at pentagon vertices around the Message Pool table
- **Judge (Judy):** Far right

### 2.2 Layout Coordinates (`layout.ts`)

```typescript
// Cluster center for the specialist pentagon
const CLUSTER_CX = 620;
const CLUSTER_CY = 260;
const PENTAGON_R = 170;  // Radius from cluster center to specialist nodes

// Pentagon angle offsets (top → right → bottom-right → bottom-left → left)
const PENTAGON_ANGLES = [-90, -18, 54, 126, 198]; // degrees

export const AGENT_POSITIONS: Record<AgentName, { x: number; y: number }> = {
  claims:       { x: 80,  y: CLUSTER_CY },        // Left, close to orchestrator
  orchestrator: { x: 280, y: CLUSTER_CY },         // Left of center
  geography:    pentagonPoint(0),                   // Top of pentagon
  legal:        pentagonPoint(1),                   // Upper-right
  news_media:   pentagonPoint(2),                   // Lower-right
  academic:     pentagonPoint(3),                   // Lower-left
  data_metrics: pentagonPoint(4),                   // Upper-left
  message_pool: { x: CLUSTER_CX - 10, y: CLUSTER_CY + 50 }, // Center of pentagon
  judge:        { x: 960, y: CLUSTER_CY },         // Far right
};
```

### 2.3 LAYOUT_CONFIG

```typescript
export const LAYOUT_CONFIG = {
  nodeWidth: 120,
  nodeHeight: 140,
  nodeSpacing: 50,
};
```

### 2.4 Node Sizing

- **EggAvatarNode:** SVG avatar ~100px × 120px; reasoning text in a `160px` wide container below
- **MessagePoolNode:** `180px × 120px` rounded rectangle; `z-index: -1` (agents render on top)
- **AgentNavBar avatar icons:** 38px × 38px minimum hit targets

---

## 3. EggAvatarNode Component

### 3.1 Overview

`EggAvatarNode` is a custom React Flow node that replaces the rectangular `AgentNode` from the v1.0 spec. It wraps the `EggAvatar` component exported from `AgentVillage.tsx` and appends a container for the most recent pulsating reasoning text.

### 3.2 Node Data Interface

```typescript
interface EggAvatarNodeData {
  agentName: AgentName;
  status: 'idle' | 'working' | 'completed' | 'error';
  reasoningMessages: string[];   // All historical messages
  latestReasoning: string;       // Most recent message for display
  findings: AgentFinding[];
  agentSpecificContent?: unknown;
}
```

### 3.3 Structure

```typescript
export function EggAvatarNode({ data, id }: NodeProps<EggAvatarNodeData>) {
  const agent = AGENTS.find(a => a.agentKey === data.agentName);

  return (
    <div className="egg-avatar-node">
      {/* React Flow connection handles (hidden visually) */}
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />

      {/* Avatar -- uses EggAvatar from AgentVillage */}
      <div className="egg-avatar-node__avatar">
        <EggAvatar agent={agent} size={100} />
        </div>

      {/* Pulsating reasoning text */}
      <div className={`egg-avatar-node__reasoning ${
        data.status === 'working' ? 'egg-avatar-node__reasoning--pulsing' : ''
      }`}>
        {data.latestReasoning || ''}
        </div>
    </div>
  );
}
```

### 3.4 Reasoning Text Animation

- **Active (status = `working`):** Text has a CSS `pulse-opacity` keyframe animation (`opacity 0.8 → 1 → 0.8`, 2s cycle)
- **Completed (status = `completed`):** Animation class removed; text is static; opacity `0.5` (dimmed)
- **Idle:** No text shown until first message arrives

### 3.5 Float Animation

`EggAvatar` has an internal continuous float animation using Framer Motion `useMotionValue` + `useAnimationFrame`. The hover scale effect is applied as a separate `whileHover` motion value so that hovering in and out does not snap the avatar back to its float start position.

---

## 4. MessagePoolNode Component

### 4.1 Overview

`MessagePoolNode` is a custom React Flow node that renders a light, semi-transparent table at the center of the specialist pentagon, representing the shared LangGraph state through which all inter-agent messages flow.

### 4.2 Node Data Interface

```typescript
interface MessagePoolNodeData {
  messages: Array<{
    type: 'info_request' | 'info_response';
    from: AgentName;
    to: AgentName;
    description: string;
    timestamp: string;
  }>;
}
```

### 4.3 Visual Design

- **Background:** `rgba(255, 246, 233, 0.85)` (warm cream, slightly opaque)
- **Border:** `1px solid rgba(224, 212, 191, 0.6)` (subtle warm border)
- **Border radius:** `8px`
- **Dimensions:** `180px × 120px` (fixed)
- **z-index:** `-1` -- agent avatars render visually on top of the table
- **Content:** Last 3 messages displayed as compact rows (type icon, from→to, truncated description)
- **Empty state:** Shows "Message Pool" label with a muted description

### 4.4 Interaction

The MessagePoolNode is non-interactive (no click handler). It is a read-only visualization.

---

## 5. VillageBackground Component

### 5.1 Overview

`VillageBackground.tsx` renders decorative SVG elements on the canvas to reinforce the "detective village" metaphor. Elements include huts, trees, and a winding path.

### 5.2 Design Constraints

- **Opacity:** 11% maximum -- purely decorative, must not compete with agent nodes or edges
- **Colors:** Warm browns only (`#8b7355`, `#6b5344`)
- **Position:** Fixed relative to the canvas background, not to React Flow's coordinate system
- **Performance:** Pure SVG (no animation); renders once

---

## 6. Custom ClaimEdge Component

### 6.1 Overview

`ClaimEdge.tsx` handles all three edge types via a single component. Edge type is passed through `data.edgeType` and determines the path calculation method and visual style.

### 6.2 Edge Types

| Edge Type | Path Method | Stroke Style | Color | Label |
|---|---|---|---|---|
| `claim` | `getStraightPath` | Solid | Source agent hex color | None |
| `infoRequest` | `getStraightPath` | Dashed (`4,3`) | Orchestrator color (`#b8a99a`) | None |
| `reinvestigation` | Custom quadratic bezier (swoop under) | Dashed (`8,4`) | Judge color (`#c0392b`) | "Cycle N" |

### 6.3 Reinvestigation Swoop-Under Path

The reinvestigation edge from Judge to Orchestrator follows a custom quadratic bezier that dips well below the specialist cluster, avoiding the pentagon:

```typescript
const REINVESTIGATION_SWOOP_Y = CLUSTER_CY + 320; // Far below the pentagon

// Custom quadratic bezier path
const midX = (sourceX + targetX) / 2;
const d = `M ${sourceX},${sourceY} Q ${midX},${REINVESTIGATION_SWOOP_Y} ${targetX},${targetY}`;
```

### 6.4 Particle Animation

Each edge has a `ParticleAnimation` SVG overlay that animates small circles along the path using CSS `offset-path` / `offset-distance`:

- **Particle radius:** 3px
- **Count:** 3 (low volume) to 8 (high volume)
- **Color:** Source agent hex color
- **Speed:** 2s base duration, linear, infinite repeat
- **Opacity:** 0.8

### 6.5 Visual Weights

| Property | `claim` | `infoRequest` | `reinvestigation` |
|---|---|---|---|
| `strokeWidth` | 1.5 | 1.5 | 2 |
| `strokeOpacity` | 0.65 | 0.65 | 0.8 |
| Animation | Pulse on working | Pulse on working | Pulse always |

---

## 7. AgentDetailSheet Component

### 7.1 Overview

`AgentDetailSheet.tsx` is the primary detail interaction for the dashboard. It slides up from the bottom of the graph canvas (beneath the AgentNavBar) when an agent avatar is clicked, displaying the agent's complete investigation history.

### 7.2 Trigger

The sheet opens when:
- A user clicks an `EggAvatarNode` directly on the graph canvas
- A user clicks a small avatar icon in the `AgentNavBar`

Both actions set `selectedAgentId` in `DashboardGraph`'s local state.

### 7.3 Layout

```
┌────────────────────────────────────────────────────────┐
│  [Mini EggAvatar]  Agent Name   Role   Status badge    │  ← Header
│                                              [×]        │
├────────────────────────────────────────────────────────┤
│  Reasoning │ Findings │ Agent-Specific                  │  ← Tabs
├────────────────────────────────────────────────────────┤
│                                                         │
│  [Tab content — scrollable]                             │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### 7.4 Tab Content

**Reasoning tab:** Full scrollable list of all reasoning messages from the agent, newest at the bottom. Messages are timestamped. If no messages, shows a placeholder.

**Findings tab:** Summary of findings produced by the agent. For agents with no findings yet, shows a placeholder.

**Agent-Specific tab** (shown only when applicable):

| Agent | Content |
|---|---|
| Geography (Columbo) | Satellite image references, location names |
| Legal (Mike) | IFRS coverage bars per pillar (green/orange/grey) |
| Data/Metrics (Rhea) | Consistency check list with pass/fail |
| Judge (Judy) | Verdict cards with color-coded badges and cycle counts |

### 7.5 Z-Index Layering

The layering order from top to bottom is:

1. **AgentNavBar** (`z-index: 60`, `position: absolute; bottom: 0`) -- always on top
2. **AgentDetailSheet** (`z-index: 50`, `position: absolute; bottom: 0`) -- slides up beneath nav bar
3. **ReactFlow canvas** (default stacking context) -- below both

The sheet's `bottom` position accounts for the nav bar height so it appears to emerge from beneath it.

### 7.6 Close Button

The close button (`×`) uses `color: #8b7355` and `hover:color: #4a3c2e`. No padded background on hover (removed `hover:bg-[#eddfc8]`).

### 7.7 Animation

```typescript
// Framer Motion AnimatePresence variant
const sheetVariants = {
  hidden: { y: '100%', opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { y: '100%', opacity: 0, transition: { duration: 0.2 } },
};
```

---

## 8. AgentNavBar Component

### 8.1 Overview

`AgentNavBar` is a horizontal bar fixed at the absolute bottom of the graph canvas wrapper. It shows all agents as small clickable avatar icons and provides an always-visible way to open the detail sheet for any agent.

### 8.2 Layout

```
┌──────────────────────────────────────────────────────────────┐
│  [Menny] [Bron] [Columbo] [Mike] [Izzy] [Newton] [Rhea] [Judy] │
└──────────────────────────────────────────────────────────────┘
```

### 8.3 Styling

- **Position:** `absolute; bottom: 0; left: 0; right: 0`
- **Background:** `rgba(255, 246, 233, 0.92)` with `backdrop-filter: blur(4px)`
- **Padding:** `4px` top/bottom
- **Item min-width:** `38px`; padding `2px`
- **z-index:** `60` (above AgentDetailSheet)
- **`position: relative` on parent** is required for `z-index` to apply

### 8.4 Status Indicators

Each nav bar avatar shows a small colored dot below it indicating the agent's current status:
- **Working:** Pulsing amber dot
- **Completed:** Static emerald dot
- **Error:** Static rose dot
- **Idle:** No dot

---

## 9. SSE Event Processing and State (useDashboard)

### 9.1 Overview

`useDashboard.ts` is the central state management hook for the dashboard. It consumes SSE events from `useSSE`, derives React Flow nodes and edges, and manages the display state for each agent.

### 9.2 Hook Signature

```typescript
interface UseDashboardReturn {
  nodes: Node[];
  edges: Edge[];
  pipelineCompleted: boolean;
}

export function useDashboard(reportId: string): UseDashboardReturn;
```

Note: `reportId` is now a required parameter (unlike v1.0 spec) because it is used as the cache key.

### 9.3 State Structure

```typescript
interface NodeData {
  agentName: AgentName;
  status: 'idle' | 'working' | 'completed' | 'error';
  latestReasoning: string;
  reasoningMessages: string[];
  findings: AgentFinding[];
  agentSpecificContent?: unknown;
}

interface GraphState {
  nodeData: Map<AgentName, NodeData>;
  edges: Edge[];
  pipelineCompleted: boolean;
}
```

### 9.4 Event Processing

```typescript
function applyEvent(state: GraphState, event: StreamEvent): GraphState {
  switch (event.event_type) {
    case 'agent_started':
      // Set agent status → 'working'
    case 'agent_thinking':
      // Append message to reasoningMessages, update latestReasoning
    case 'claim_routed':
      // Add claim edge from orchestrator to target agent(s)
    case 'evidence_found':
      // Update agent findingsCount; add edge from agent to judge
    case 'reinvestigation':
      // Add reinvestigation edge from judge to orchestrator with cycle count
    case 'info_request_routed':
      // Add infoRequest edge from requesting agent through orchestrator to target
    case 'agent_completed':
      // Set agent status → 'completed'
    case 'pipeline_completed':
      // Set ALL working agents → 'completed'; set pipelineCompleted = true
    case 'error':
      // Set agent status → 'error'
  }
}
```

### 9.5 Nodes Derivation

Nodes are derived from `GraphState.nodeData` using `useMemo`. Each agent in `ALL_AGENTS` always has a node (initialized to `idle` status). Node positions come from `AGENT_POSITIONS` in `layout.ts`. The `message_pool` node uses `nodeType: 'messagePool'`; all others use `nodeType: 'eggAvatar'`.

The `message_pool` node has `zIndex: -1` to ensure avatar nodes render on top.

---

## 10. State Persistence (Module-Level Caches)

### 10.1 Motivation

When a user navigates away from the Analysis page and returns, both the SSE connection and the React component tree are destroyed. Without persistence, all reasoning history and graph state would be lost. Module-level caches (stored outside any React component, in the module scope) survive navigation and restore state on remount.

### 10.2 SSE Event Cache (`useSSE.ts`)

```typescript
// Module-level: survives component unmount/remount
const eventCache = new Map<string, StreamEvent[]>();

export function useSSE(reportId: string) {
  const [events, setEvents] = useState<StreamEvent[]>(
    () => eventCache.get(reportId) ?? []  // Initialize from cache
  );

  // On new events: append to state AND update cache
  const handleEvent = (event: StreamEvent) => {
    setEvents(prev => {
      const updated = [...prev, event];
      eventCache.set(reportId, updated);
      return updated;
    });
  };

  // clearEvents also clears the cache entry
  const clearEvents = () => {
    eventCache.delete(reportId);
    setEvents([]);
  };
}
```

### 10.3 Graph State Cache (`useDashboard.ts`)

```typescript
// Module-level
const graphStateCache = new Map<string, GraphState>();

export function useDashboard(reportId: string) {
  const [graphState, dispatch] = useReducer(
    graphStateReducer,
    graphStateCache.get(reportId) ?? initialGraphState  // Initialize from cache
  );

  // On every state change, write back to cache
useEffect(() => {
    graphStateCache.set(reportId, graphState);
  }, [reportId, graphState]);
}
```

### 10.4 Scope

Both caches are scoped to the browser session (in-memory JavaScript `Map`). They do not persist across page reloads. A full reload clears caches and reconnects SSE from scratch.

---

## 11. Confetti and Completion

### 11.1 Trigger

When `useDashboard` detects `pipelineCompleted = true` for the first time (guarded by a `useRef` to prevent double-firing), `DashboardGraph` fires confetti.

### 11.2 Implementation

`canvas-confetti` is loaded via dynamic import to avoid Vite static analysis issues:

```typescript
const confettiFired = useRef(false);

  useEffect(() => {
  if (pipelineCompleted && !confettiFired.current) {
    confettiFired.current = true;
    import('canvas-confetti').then(({ default: confetti }) => {
      // Left side
      confetti({ particleCount: 80, angle: 60, spread: 55, origin: { x: 0 } });
      // Right side
      confetti({ particleCount: 80, angle: 120, spread: 55, origin: { x: 1 } });
    });
  }
}, [pipelineCompleted]);
```

### 11.3 Agent Status on Completion

`pipeline_completed` SSE event causes `useDashboard` to set all agents currently in `'working'` status to `'completed'`. This also stops the reasoning text pulsing animation (the `--pulsing` CSS class is tied to `status === 'working'`).

---

## 12. Analysis Page Integration

### 12.1 Page Layout

`AnalysisPage.tsx` hosts the entire analysis experience. Key structural decisions:

- **Height:** `calc(100vh - 56px)` -- pinned exactly to the viewport minus the global header; the page is self-contained and non-scrollable
- **Split:** Left graph pane (default 75%) / Right reasoning panel (default 25%) via `ResizableSplit`
- **Tabs:** "Document" (PDF viewer) and "Investigation" (detective dashboard)
- **Investigation tab nudge:** A pulsating dot on the Investigation tab appears after upload, guiding users to explore the live graph

### 12.2 Graph Container

The graph pane passes `reportId` to `DashboardGraph`:

```typescript
<DashboardGraph reportId={reportId} />
```

### 12.3 Width

The graph container has no `max-width` constraint. CSS overrides in `AnalysisPage.css` ensure `.analysis-page__main`, `.analysis-page__header-content`, and `.analysis-split` all use `max-width: none; margin: 0; width: 100%` to fill the viewport edge-to-edge.

### 12.4 AgentReasoningPanel (Right Panel)

The right panel (`AgentReasoningPanel.tsx`) continues to show:
- Tabbed agent event log (all agents + individual tabs)
- Live reasoning stream from the active agent
- A "Pipeline complete — View Report" button (styled to match the "Begin Analysis" button) when `pipelineCompleted` is true

Event history in this panel is also restored from the SSE event cache on navigation.

---

## 13. Animation System

### 13.1 Avatar Float

Each `EggAvatar` uses Framer Motion's `useMotionValue` + `useAnimationFrame` to run a continuous sinusoidal float animation. The float runs independently of hover effects. On hover, `whileHover={{ scale: 1.08 }}` is applied as a separate transform. When the user hovers off, the float continues from wherever it currently is (no snap-back).

Implementation key: the continuous float updates `y` via `useAnimationFrame` at 60fps without triggering React re-renders, while Framer Motion's `useTransform` composes the hover scale on top.

### 13.2 Reasoning Text Pulse

```css
@keyframes pulse-opacity {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

.egg-avatar-node__reasoning--pulsing {
  animation: pulse-opacity 2s ease-in-out infinite;
}
```

### 13.3 Bottom Sheet Slide-Up

Framer Motion `AnimatePresence` + `motion.div` with `y: '100%' → y: 0` transition (0.3s ease-out for enter, 0.2s for exit).

### 13.4 List Page Stagger Animations

Analysis and Report list pages use Framer Motion `variants` with `staggerChildren: 0.05s` to fade list items in one after another (0.22s fade per item, `opacity: 0 → 1`, `y: 8 → 0`).

### 13.5 Edge Particles

SVG `<circle>` elements animated via CSS `offset-path` / `offset-distance: 0% → 100%`. Each particle has a staggered `animation-delay` to distribute them along the path.

---

## 14. Design System Compliance

All dashboard components must follow the warm cream design system (PRD 7.1 / `design-system.md`):

| Rule | Application in Dashboard |
|---|---|
| Background `#fff6e9` | Graph canvas background; AgentNavBar; AgentDetailSheet |
| Body text `#4a3c2e` | Reasoning text, agent names, sheet content |
| Muted text `#8b7355` | Timestamps, finding counts, placeholder text |
| Muted surface `#eddfc8` | AgentDetailSheet tab active state |
| Borders `#e0d4bf` | Sheet header border, tab borders |
| No `rounded-xl` on content cards | AgentDetailSheet uses `rounded-t-2xl` only on the top corners (it's a sheet from the bottom) |
| No cold greys | No `slate-*` anywhere in dashboard components |
| Lucide React icons only | All icons (close X, status dots) use Lucide |
| No emoji | Agent marks are SVG paths via `AgentMark`, not emoji |

Agent hex colors (for node borders, edge strokes, particles) are defined in `AGENT_HEX_COLORS` in `layout.ts` and match the PRD 7.1 agent color identity table.

---

## 15. Error and Edge Case Handling

### 15.1 Missing Events

| Scenario | Handling |
|---|---|
| `agent_started` missing | Infer activation from first `agent_thinking` event for that agent |
| `agent_completed` missing for a specialist | `pipeline_completed` sets all working agents to completed |
| Events arrive out of order | SSE events are appended in arrival order; the backend guarantees chronological emission |

### 15.2 Agent Failures

| Scenario | Handling |
|---|---|
| `error` event for an agent | Agent status → `'error'`; reasoning text shows last known message |
| Agent produces no findings | Findings tab shows "No findings yet" placeholder |

### 15.3 Network Disconnections

| Scenario | Handling |
|---|---|
| SSE connection lost | `useSSE` auto-reconnects via `EventSource` native reconnection |
| User navigates away mid-stream | Module-level cache preserves all events received so far; on return, cache is replayed |

### 15.4 Empty Graph

If no events have been received (e.g., analysis hasn't started):
- All agents show `idle` status (no reasoning text)
- Edges are empty
- Village background and avatar nodes still render

### 15.5 Avatar Hover Snap-Back Bug (Fixed)

The original `AgentVillage.tsx` used a single Framer Motion animation that included both the float and the hover state, causing the avatar to snap back to the float start position when the cursor left. The fix separates float (driven by `useAnimationFrame` on a `useMotionValue`) from hover (driven by `whileHover`) so they compose independently.

---

## 16. Exit Criteria

FRD 12 (v2.0) is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Egg-shaped avatar nodes render for all 8 agents | Navigate to `/analysis/{reportId}`; verify all avatars are visible |
| 2 | Specialist agents are arranged in a pentagon | Verify pentagon formation around Message Pool table |
| 3 | Message Pool table is centered in the pentagon | Verify table is visually centered; agents render on top |
| 4 | Claims agent is positioned left, near Orchestrator | Verify Menny appears close to Bron on the left |
| 5 | Judge is on the far right | Verify Judy appears rightmost |
| 6 | VillageBackground renders at low opacity | Verify decorative SVG elements are barely visible behind nodes |
| 7 | Pulsating reasoning text appears under active avatars | Trigger analysis; verify text pulses below each active avatar |
| 8 | Reasoning text stops pulsing on completion | Verify all text becomes static after `pipeline_completed` |
| 9 | Clicking an avatar opens the bottom sheet | Click any avatar; verify AgentDetailSheet slides up |
| 10 | Bottom sheet shows full reasoning history | Verify all messages are present, scrollable |
| 11 | Bottom sheet tabs work (Reasoning / Findings / Agent-Specific) | Click each tab; verify content changes |
| 12 | AgentNavBar is visible at the bottom | Verify small avatar icons are visible below the graph |
| 13 | Clicking a nav bar icon opens the sheet | Click each icon; verify correct agent's sheet opens |
| 14 | Bottom sheet layers below AgentNavBar | Verify nav bar remains visible when sheet is open |
| 15 | Close button has no hover background | Hover over `×`; verify no brown box appears |
| 16 | Straight edges connect agents for claim flow | Verify solid straight lines appear as claims are routed |
| 17 | Reinvestigation edge swoops under the cluster | Trigger reinvestigation; verify arc goes below all specialist nodes |
| 18 | InfoRequest edges are dashed | Verify dashed style on info request edges |
| 19 | Particle animations flow along edges | Verify animated circles travel along edge paths |
| 20 | Confetti fires on pipeline completion | Verify confetti from both sides when `pipeline_completed` arrives |
| 21 | "View Report" button appears on completion | Verify button in AgentReasoningPanel after completion |
| 22 | Graph fills the full left pane width | Verify no cream whitespace gaps to the left of the graph |
| 23 | AgentNavBar is never cut off | Verify nav bar is fully visible without scrolling |
| 24 | Analysis page is not scrollable | Verify the page does not allow vertical scroll |
| 25 | SSE events are cached across navigation | Navigate away and back; verify reasoning history persists |
| 26 | Graph state is cached across navigation | Navigate away and back; verify node statuses and edges persist |
| 27 | Avatar float animation is not disrupted by hover | Hover on and off an avatar; verify float continues from current position |
| 28 | Agent colors match PRD 7.1 palette | Verify each avatar border and edge particle color matches the spec |
| 29 | No cold grey colors used anywhere | Audit dashboard CSS for any `slate-*` or `#6b7280` equivalents |
| 30 | Warm cream design system compliance | Verify background, text, borders all use warm cream palette |

---

## Appendix A: Agent Roster

| Agent | Avatar Name | Avatar Mark | Hex Color |
|---|---|---|---|
| Claims | Menny | document | `#7c9cbf` |
| Orchestrator | Bron | network | `#b8a99a` |
| Geography | Columbo | globe | `#6aaa64` |
| Legal | Mike | scale | `#9b6dd0` |
| News/Media | Izzy | wifi | `#e8b84b` |
| Academic/Research | Newton | flask | `#4db6ac` |
| Data/Metrics | Rhea | bar-chart | `#e8855a` |
| Judge | Judy | gavel | `#c0392b` |

---

## Appendix B: Graph Layout Coordinates

### B.1 Pentagon Geometry

```
Cluster center: (620, 260)
Pentagon radius: 170px

Agent positions (approximate):
  Geography (top):       (620, 90)
  Legal (upper-right):   (777, 208)
  News/Media (lower-right): (719, 390)
  Academic (lower-left): (521, 390)
  Data/Metrics (upper-left): (463, 208)
  Message Pool (center): (610, 310)

Left side:
  Claims:       (80, 260)
  Orchestrator: (280, 260)

Right side:
  Judge: (960, 260)
```

### B.2 LAYOUT_CONFIG

```typescript
export const LAYOUT_CONFIG = {
  nodeWidth: 120,
  nodeHeight: 140,
  nodeSpacing: 50,
};
```

---

## Appendix C: SSE Event to Graph Update Mapping

| SSE Event Type | Graph Update | Details |
|---|---|---|
| `agent_started` | Set node status → `working` | Starts reasoning text pulsing |
| `agent_thinking` | Append to `reasoningMessages`; update `latestReasoning` | Live reasoning text updates |
| `claim_routed` | Add `claim` edge from orchestrator to target agent(s) | Straight line in orchestrator color |
| `evidence_found` | Update agent findings count; add `claim` edge from agent to judge | Straight line in agent color |
| `reinvestigation` | Add `reinvestigation` edge from judge to orchestrator | Swoop-under dashed crimson arc with cycle badge |
| `info_request_routed` | Add `infoRequest` edges through orchestrator | Dashed lines in orchestrator color |
| `info_response_posted` | (No new edge; info request edge already present) | Response stored in message pool messages |
| `agent_completed` | Set node status → `completed` | Stops reasoning pulsing for this agent |
| `pipeline_completed` | All working agents → `completed`; `pipelineCompleted = true` | Triggers confetti; stops all pulsing |
| `error` | Set node status → `error` | Error color indicator on avatar |

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Egg-shaped avatars over rectangular blocks | Avatars bring personality and warmth to the investigation process, matching the "detective village" metaphor. Characters named Menny, Bron, Columbo, etc. are more memorable and approachable than generic agent boxes. |
| Warm cream theme over dark theme | The Sibyl design system is warm cream throughout. The original dark-theme graph would have been visually inconsistent with every other page in the application. |
| Horizontal layout over vertical | Left-to-right matches natural reading direction of the pipeline flow (claims → orchestrate → investigate → judge). The horizontal layout also makes better use of widescreen viewport space. |
| Pentagon layout for specialists over horizontal row | A row of 5 agents becomes very wide. A pentagon clusters them naturally around the shared Message Pool, making the inter-agent communication metaphor visually intuitive. |
| MessagePoolNode as in-graph React Flow node over floating overlay | An in-graph node participates in the React Flow coordinate system, so it stays correctly positioned during zoom/pan. A floating overlay (position: absolute) would need manual coordinate synchronization. |
| Bottom sheet over click-to-expand nodes | Expanding nodes inside the graph causes layout reflow and potentially overlaps other nodes. A bottom sheet provides ample space for full detail without disturbing the graph. It also follows a familiar mobile/web UX pattern. |
| AgentNavBar at fixed bottom over inline expand | A fixed navigator bar lets users switch between agents rapidly without having to click through the graph. It persists regardless of zoom/pan state. |
| Module-level caches over localStorage | localStorage has synchronous I/O and a 5MB limit. Module-level Maps are fast, unlimited (up to process memory), and sufficient for a single-session use case. Full cross-session persistence would require a database endpoint. |
| Dynamic import for canvas-confetti | Vite's static import analysis fails if the package isn't installed in the container's node_modules at build time. Dynamic import defers resolution to runtime, preventing build errors. |
| Straight edges for claim/infoRequest over bezier | Straight edges are cleaner and less visually busy when there are many edges in a dense pentagon layout. Bezier curves would cross through the Message Pool table. Reinvestigation still uses a bezier for its swoop-under effect. |
| Swoop-under path for reinvestigation | The reinvestigation edge from Judge (right) to Orchestrator (left-center) would normally cross through the entire specialist pentagon. Swooping below the cluster keeps the path clean and makes the cycle visually distinct. |
| Confetti on pipeline_completed | Completing an investigation is a significant milestone. Confetti provides genuine delight and clearly communicates success without requiring the user to read status text. |
| Separate float and hover animations | Combining float and hover in one Framer Motion `animate` caused the avatar to snap back to the float start position when hovering ended. Separating them (float via `useAnimationFrame`, hover via `whileHover`) ensures the animations compose independently. |
| `height: calc(100vh - 56px)` for AnalysisPage | Pinning the page to an exact height prevents the global `overflow-auto` on `<main>` from allowing page-level scrolling, while not affecting any other page in the application. 56px matches the global header height. |

---

*This FRD (v2.0) documents the implemented Detective Dashboard as of 2026-02-27. It supersedes v1.0 in its entirety. The v1.0 specification described the originally planned design (dark rectangular blocks, vertical pipeline layout, click-to-expand nodes); the actual implementation chose the warm cream avatar village design described here.*
