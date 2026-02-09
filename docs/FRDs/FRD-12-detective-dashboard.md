# Feature Requirements Document: FRD 12 -- Detective Dashboard (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.10 (Detective Dashboard), 7.2 (Analysis Page center panel) |
| **Type** | Feature |
| **Depends On** | FRD 5 (Orchestrator Agent & LangGraph Pipeline), FRDs 6-11 (all specialist agents + Judge) |
| **Delivers** | Real-time React Flow network graph visualization with agent nodes, claim/evidence edges, agent-specific displays, node/edge interactions, cyclic validation visualization, inter-agent communication visualization, animation system, Analysis Page center panel integration |
| **Created** | 2026-02-09 |

---

## Summary

FRD 12 delivers the Detective Dashboard -- the hero visual of Sibyl that exposes the full multi-agent investigation process to users in real time through an interactive, animated network graph. The dashboard (`src/components/Dashboard/DashboardGraph.tsx`) replaces the FRD 5 center panel placeholder with a fully functional React Flow (`@xyflow/react`) network graph visualization displaying agent nodes arranged in pipeline flow (Claims → Orchestrator → Specialists → Judge → Report), custom `AgentNode.tsx` components with unique agent colors and status indicators (pulsing animation for active, solid for idle, checkmark for complete, warning icon for error), custom `ClaimEdge.tsx` components with animated particles showing data flow direction and volume, real-time updates driven by SSE events from the LangGraph pipeline (FRD 5), expandable node interactions revealing agent reasoning streams, findings summaries, claim counts, and agent-specific content, clickable edge interactions showing the messages or data being passed between agents, agent-specific display components (Geography Agent: `SatelliteImageTile.tsx` with satellite imagery from MPC, Legal Agent: `IFRSCoverageBar.tsx` with progress bars per pillar, Data/Metrics Agent: `ConsistencyCheckList.tsx` with running pass/fail indicators, Judge Agent: `VerdictCard.tsx` with color-coded verdict badges and cycle counts), cyclic validation visualization with distinct re-investigation loop animations between Judge and Orchestrator, inter-agent communication visualization showing InfoRequest/Response edges flowing through the Orchestrator, a comprehensive animation system (pulsing nodes, flowing particles, cycle indicators), seamless integration with the Analysis Page center panel replacing the placeholder, state management via `useDashboard` hook deriving graph state from SSE events, performance optimizations (React Flow memoization, virtualization for large graphs), and robust error handling. The dashboard consumes SSE events from FRD 5's streaming infrastructure, displays findings from all specialist agents (FRDs 6-10), visualizes Judge verdicts and re-investigation cycles (FRD 11), and serves as the primary interface for users to watch the investigation unfold in real time. After FRD 12, users watch the full investigation through an animated, interactive network graph with agent-specific displays and clickable nodes/edges, making Sibyl's investigative process fully transparent and auditable.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| LangGraph StateGraph with all nodes (Claims, Orchestrator, Geography, Legal, News/Media, Academic, Data/Metrics, Judge) | FRD 5, FRDs 6-11 | `app/agents/graph.py` |
| SSE streaming infrastructure with `StreamEvent` emission and FastAPI SSE endpoint | FRD 5 | `app/api/routes/stream.py`, `app/agents/callbacks.py` |
| `useSSE` hook for consuming SSE events in React | FRD 5 | `src/hooks/useSSE.ts` |
| `StreamEvent` TypeScript types matching backend schema | FRD 5 | `src/types/agent.ts` |
| Analysis Page three-panel layout with center panel placeholder | FRD 4 | `src/pages/AnalysisPage.tsx`, `src/components/Analysis/AnalysisLayout.tsx` |
| Agent color system (CSS variables for each agent) | FRD 0, PRD 7.1 | `src/app.css` |
| Geography Agent findings with satellite image references (MPC STAC Item URLs) | FRD 10 | `AgentFinding.details.image_references` |
| Legal Agent findings with IFRS coverage data per pillar | FRD 6 | `AgentFinding.details.ifrs_coverage` |
| Data/Metrics Agent findings with consistency check results | FRD 7 | `AgentFinding.details.consistency_checks` |
| Judge Agent findings with verdicts and cycle counts | FRD 11 | `AgentFinding.details.verdicts`, `iteration_count` |
| Inter-agent communication events (`info_request_posted`, `info_request_routed`, `info_response_posted`) | FRD 5 | `StreamEvent` types |
| Re-investigation events (`reinvestigation`) with cycle numbers | FRD 11 | `StreamEvent` types |
| `@xyflow/react` installed as a frontend dependency | FRD 0 | `package.json` |
| React Flow CSS imported | FRD 0 | `src/app.css` or `src/main.tsx` |
| `AgentName`, `AgentStatus`, `AgentFinding` TypeScript types | FRD 0, FRD 5 | `src/types/agent.ts` |
| `Claim`, `ClaimType` TypeScript types | FRD 3 | `src/types/claim.ts` |
| API client with SSE connection method | FRD 5 | `src/services/sse.ts` |

### Terms

| Term | Definition |
|---|---|
| React Flow | A library (`@xyflow/react`) for building node-based UI graphs, providing canvas rendering, zoom/pan, node/edge interactions, and layout algorithms |
| Agent node | A React Flow node component representing a single agent (Claims, Orchestrator, Geography, Legal, News/Media, Academic, Data/Metrics, Judge) with visual status indicators and expandable content |
| Claim edge | A React Flow edge component representing data flow (claims, evidence, requests) between agents, with animated particles showing direction and volume |
| Node expansion | User interaction where clicking an agent node expands it to reveal detailed content (reasoning stream, findings, agent-specific displays) |
| Edge interaction | User interaction where clicking a claim edge reveals a popover showing the specific message or data being passed |
| Cyclic validation loop | Visual representation of the re-investigation cycle where the Judge sends claims back to the Orchestrator, shown as a distinct animated edge |
| Inter-agent communication edge | Visual representation of InfoRequest/Response flows routed through the Orchestrator, distinct from claim routing edges |
| Agent-specific display | Domain-specific visual content rendered within an agent node (satellite imagery, IFRS progress bars, consistency checks, verdict cards) |
| Graph layout | The spatial arrangement of nodes and edges on the canvas, computed algorithmically to show pipeline flow and relationships |
| Particle animation | Animated particles flowing along edges to indicate data movement direction and volume |
| Status indicator | Visual element showing agent state: pulsing animation (active), solid color (idle), checkmark icon (complete), warning icon (error) |
| Graph state | React state derived from SSE events, tracking node positions, edge connections, agent statuses, and displayed content |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Detective Dashboard -- Real-Time Agent Visualization

  Background:
    Given  FRD 5, FRDs 6-11 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    a sustainability report analysis is running or completed
    And    SSE events are streaming from the LangGraph pipeline
    And    the Analysis Page three-panel layout is displayed

  Scenario: Render the network graph in the center panel
    Given  the user navigates to /analysis/{reportId}
    When   the Analysis Page loads
    Then   the center panel displays a React Flow network graph
    And    agent nodes are arranged in pipeline flow: Claims at top, Orchestrator below, specialists in a row, Judge at bottom
    And    edges connect nodes showing claim/evidence flow
    And    the graph is zoomable and pannable

  Scenario: Display agent nodes with status indicators
    Given  the network graph is rendered
    When   agents are active in the pipeline
    Then   each agent node displays its unique color identity
    And    active agents show a pulsing animation
    And    idle agents show solid color
    And    completed agents show a checkmark icon
    And    errored agents show a warning icon
    And    each node displays the agent name and current status

  Scenario: Expand agent nodes to see details
    Given  an agent node is displayed
    When   the user clicks on the node
    Then   the node expands to reveal:
      - Agent status and reasoning stream
      - Findings summary and claim count
      - Agent-specific display (if applicable)
    And    clicking another node collapses the previous node
    And    clicking outside collapses all nodes

  Scenario: Display Geography Agent satellite imagery
    Given  the Geography Agent node is expanded
    When   the agent has processed geographic claims
    Then   the node displays a satellite image tile
    And    the tile shows the location name, coordinates, and imagery date
    And    for temporal claims, before/after image pairs are shown
    And    clicking the image opens a larger view or MPC link

  Scenario: Display Legal Agent IFRS coverage progress
    Given  the Legal Agent node is expanded
    When   the agent has assessed IFRS compliance
    Then   the node displays IFRS coverage progress bars per pillar
    And    each pillar shows: Governance, Strategy, Risk Management, Metrics & Targets
    And    progress bars use green (covered), orange (partial), grey (gaps)
    And    each bar shows coverage percentage and paragraph counts

  Scenario: Display Data/Metrics Agent consistency checks
    Given  the Data/Metrics Agent node is expanded
    When   the agent has validated quantitative claims
    Then   the node displays a running list of consistency checks
    And    each check shows: description, pass/fail indicator, result details
    And    checks include: Scope totals, percentage calculations, benchmark comparisons
    And    failed checks are highlighted in red, passed checks in green

  Scenario: Display Judge Agent verdict cards
    Given  the Judge Agent node is expanded
    When   the agent has issued verdicts
    Then   the node displays verdict cards
    And    each card shows: claim text, color-coded verdict badge, cycle count
    And    verdict badges use: green (Verified), yellow (Unverified), orange (Insufficient Evidence), red (Contradicted)
    And    cards are scrollable if many verdicts exist

  Scenario: Animate claim/evidence flow along edges
    Given  claims are being routed between agents
    When   the graph updates
    Then   animated particles flow along edges showing data movement
    And    particle density indicates volume (more particles = more claims/evidence)
    And    particle direction shows flow direction (from source to target)
    And    particles use the source agent's color

  Scenario: Click edges to see data being passed
    Given  an edge is displayed between two agents
    When   the user clicks on the edge
    Then   a popover appears showing:
      - The specific claim, evidence, or request being passed
      - Source and target agent names
      - Timestamp and event type
    And    the popover dismisses when clicking outside or pressing Escape

  Scenario: Visualize cyclic validation loops
    Given  the Judge has requested re-investigation
    When   a reinvestigation event is received
    Then   a distinct animated edge appears from Judge back to Orchestrator
    And    the edge uses a different style (dashed, different color) than regular claim edges
    And    the edge shows cycle count (e.g., "Cycle 2")
    And    an animation highlights the loop path

  Scenario: Visualize inter-agent communication
    Given  a specialist agent posts an InfoRequest
    When   the Orchestrator routes it to another agent
    Then   an edge appears from the requesting agent through Orchestrator to the responding agent
    And    the edge is labeled with the request type
    And    the edge uses a distinct style (dotted, different color) from claim edges
    And    clicking the edge shows the InfoRequest/Response content

  Scenario: Real-time graph updates from SSE events
    Given  the pipeline is executing
    When   SSE events stream to the frontend
    Then   the graph updates in real time:
      - New nodes appear as agents activate
      - Edges appear as claims are routed
      - Node status indicators update (idle → active → complete)
      - Agent-specific displays update with new findings
    And    updates occur within 500ms of event emission
    And    the graph remains interactive during updates

  Scenario: Handle graph layout for many claims
    Given  a report with 100+ claims is being analyzed
    When   the graph renders
    Then   the layout algorithm positions nodes to avoid overlap
    And    edges are routed cleanly without excessive crossings
    And    the graph remains readable and navigable
    And    performance remains smooth (60fps) during interactions

  Scenario: Integrate with Analysis Page center panel
    Given  the Analysis Page three-panel layout is displayed
    When   the center panel loads
    Then   the Detective Dashboard occupies the full center panel
    And    the panel header shows "Investigation Dashboard"
    And    the dashboard respects panel resizing
    And    zoom/pan controls are accessible within the panel
```

---

## Table of Contents

1. [React Flow Graph Architecture](#1-react-flow-graph-architecture)
2. [Graph Layout and Node Positioning](#2-graph-layout-and-node-positioning)
3. [Custom AgentNode Component](#3-custom-agentnode-component)
4. [Agent-Specific Display Components](#4-agent-specific-display-components)
5. [Custom ClaimEdge Component](#5-custom-claimedge-component)
6. [SSE Event Processing for Graph Updates](#6-sse-event-processing-for-graph-updates)
7. [Node Interaction](#7-node-interaction)
8. [Edge Interaction](#8-edge-interaction)
9. [Cyclic Validation Visualization](#9-cyclic-validation-visualization)
10. [Inter-Agent Communication Visualization](#10-inter-agent-communication-visualization)
11. [Animation System](#11-animation-system)
12. [Analysis Page Center Panel Integration](#12-analysis-page-center-panel-integration)
13. [State Management](#13-state-management)
14. [Performance Optimization](#14-performance-optimization)
15. [Error and Edge Case Handling](#15-error-and-edge-case-handling)
16. [Exit Criteria](#16-exit-criteria)
17. [Appendix A: Agent Color Palette Reference](#appendix-a-agent-color-palette-reference)
18. [Appendix B: Graph Layout Coordinates](#appendix-b-graph-layout-coordinates)
19. [Appendix C: SSE Event to Graph Update Mapping](#appendix-c-sse-event-to-graph-update-mapping)
20. [Appendix D: Animation Specifications](#appendix-d-animation-specifications)
21. [Design Decisions Log](#design-decisions-log)

---

## 1. React Flow Graph Architecture

### 1.1 Overview

The Detective Dashboard is built on React Flow (`@xyflow/react`), a library for building node-based UI graphs. The graph renders agent nodes and edges on a zoomable, pannable canvas, with custom node and edge components providing agent-specific visualizations and interactions.

### 1.2 DashboardGraph Component

```typescript
// src/components/Dashboard/DashboardGraph.tsx

import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { AgentNode } from './AgentNode';
import { ClaimEdge } from './ClaimEdge';

interface DashboardGraphProps {
  reportId: string;
  isAnalyzing: boolean;
  events: StreamEvent[];
}

const nodeTypes = {
  agent: AgentNode,
};

const edgeTypes = {
  claim: ClaimEdge,
  reinvestigation: ClaimEdge,  // Different styling
  infoRequest: ClaimEdge,      // Different styling
};

export function DashboardGraph({ reportId, isAnalyzing, events }: DashboardGraphProps) {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect } = useDashboardGraph(
    reportId,
    isAnalyzing,
    events
  );

  return (
    <ReactFlowProvider>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        minZoom={0.1}
        maxZoom={2.0}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
      >
        <Background color="#1a1a1a" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => getAgentColor(node.data.agentName)}
          maskColor="rgba(0, 0, 0, 0.6)"
        />
      </ReactFlow>
    </ReactFlowProvider>
  );
}
```

### 1.3 React Flow Configuration

| Setting | Value | Rationale |
|---|---|---|
| `fitView` | `true` | Automatically fits the graph to the viewport on initial render |
| `minZoom` | `0.1` | Allows zooming out to see the full graph layout |
| `maxZoom` | `2.0` | Allows zooming in for detailed inspection of nodes |
| `defaultViewport` | `{ x: 0, y: 0, zoom: 0.8 }` | Slightly zoomed out to show the full pipeline flow |
| `snapToGrid` | `false` | Free-form positioning for more natural layouts |
| `snapGrid` | `[20, 20]` | Grid size for manual alignment (if enabled) |
| `nodesDraggable` | `true` | Users can reposition nodes for better visibility |
| `edgesUpdatable` | `false` | Edges are computed from SSE events, not user-editable |
| `connectionLineStyle` | Custom | Styled to match claim edge appearance |

### 1.4 Graph Canvas Styling

The graph canvas uses the dark theme background:

```css
.react-flow {
  background: hsl(224, 20%, 9%);
  width: 100%;
  height: 100%;
}

.react-flow__controls {
  background: hsl(224, 20%, 14%);
  border: 1px solid hsl(224, 20%, 25%);
}

.react-flow__minimap {
  background: hsl(224, 20%, 12%);
  border: 1px solid hsl(224, 20%, 25%);
}
```

### 1.5 Background Pattern

The `Background` component provides a subtle grid pattern:

- **Color:** `#1a1a1a` (slightly lighter than canvas background)
- **Gap:** `16px` (grid spacing)
- **Variant:** `dots` (dot pattern for subtle texture)

---

## 2. Graph Layout and Node Positioning

### 2.1 Overview

The graph layout arranges agent nodes in a pipeline flow pattern: Claims at the top, Orchestrator below, specialist agents in a horizontal row, Judge at the bottom, with a visible cycle arrow back to Orchestrator. Node positions are computed algorithmically based on agent type and pipeline stage.

### 2.2 Layout Algorithm

The system shall compute node positions using a hierarchical layout:

```typescript
interface LayoutConfig {
  claimsY: number;        // Y position for Claims Agent (top)
  orchestratorY: number; // Y position for Orchestrator
  specialistsY: number; // Y position for specialist agents (middle row)
  judgeY: number;        // Y position for Judge Agent (bottom)
  nodeSpacing: number;   // Horizontal spacing between nodes
  rowSpacing: number;   // Vertical spacing between rows
}

function computeNodePositions(
  agents: AgentName[],
  config: LayoutConfig
): Map<AgentName, { x: number; y: number }> {
  const positions = new Map<AgentName, { x: number; y: number }>();

  // Claims Agent: top center
  if (agents.includes('claims')) {
    positions.set('claims', { x: 400, y: config.claimsY });
  }

  // Orchestrator: below Claims, centered
  if (agents.includes('orchestrator')) {
    positions.set('orchestrator', { x: 400, y: config.orchestratorY });
  }

  // Specialist agents: horizontal row, evenly spaced
  const specialists = agents.filter(a =>
    ['geography', 'legal', 'news_media', 'academic', 'data_metrics'].includes(a)
  );
  const specialistCount = specialists.length;
  const totalWidth = (specialistCount - 1) * config.nodeSpacing;
  const startX = 400 - totalWidth / 2;

  specialists.forEach((agent, index) => {
    positions.set(agent, {
      x: startX + index * config.nodeSpacing,
      y: config.specialistsY,
    });
  });

  // Judge: bottom center
  if (agents.includes('judge')) {
    positions.set('judge', { x: 400, y: config.judgeY });
  }

  return positions;
}
```

### 2.3 Default Layout Coordinates

| Agent | X Position | Y Position | Notes |
|---|---|---|---|
| Claims | 400 | 50 | Top center |
| Orchestrator | 400 | 200 | Below Claims, centered |
| Geography | 200 | 400 | Left side of specialist row |
| Legal | 300 | 400 | Second from left |
| News/Media | 400 | 400 | Center of specialist row |
| Academic | 500 | 400 | Second from right |
| Data/Metrics | 600 | 400 | Right side of specialist row |
| Judge | 400 | 600 | Bottom center |

Coordinates are in React Flow's coordinate system (pixels). The layout is centered horizontally with a 200px margin on each side.

### 2.4 Dynamic Layout Adjustments

The layout adjusts dynamically as agents activate:

1. **Initial state:** Only Claims and Orchestrator nodes are visible.
2. **After routing:** Specialist agent nodes appear in the middle row as they receive assignments.
3. **After investigation:** Judge node appears at the bottom.
4. **During re-investigation:** The cycle edge becomes visible from Judge back to Orchestrator.

### 2.5 Node Size

| Agent | Width | Height | Expanded Height |
|---|---|---|---|
| All agents (collapsed) | 180px | 80px | -- |
| Claims (expanded) | 320px | 400px | Varies by content |
| Orchestrator (expanded) | 320px | 350px | Varies by content |
| Specialist (expanded) | 320px | 450px | Varies by agent-specific content |
| Judge (expanded) | 320px | 500px | Varies by verdict count |

### 2.6 Layout Responsiveness

The layout adapts to panel width:

- **Wide panels (>1200px):** Full horizontal spacing (200px between specialists).
- **Medium panels (800-1200px):** Reduced spacing (150px between specialists).
- **Narrow panels (<800px):** Stack specialists vertically or use a compact horizontal layout.

---

## 3. Custom AgentNode Component

### 3.1 Overview

The `AgentNode` component (`src/components/Dashboard/AgentNode.tsx`) is a custom React Flow node that displays an agent with its unique color identity, status indicators, and expandable content panels.

### 3.2 Node Interface

```typescript
interface AgentNodeData {
  agentName: AgentName;
  status: AgentStatus;  // 'idle' | 'working' | 'completed' | 'error'
  claimsAssigned: number;
  claimsCompleted: number;
  findingsCount: number;
  reasoningStream: string[];  // Recent reasoning messages
  findings: AgentFinding[];   // Recent findings
  agentSpecificContent?: AgentSpecificContent;  // Geography: images, Legal: IFRS bars, etc.
  expanded: boolean;
}

interface AgentNodeProps {
  id: string;
  data: AgentNodeData;
  selected: boolean;
}
```

### 3.3 Node Structure

```typescript
export function AgentNode({ id, data, selected }: AgentNodeProps) {
  const { agentName, status, expanded } = data;
  const color = getAgentColor(agentName);

  return (
    <div
      className={`agent-node agent-node--${status} ${expanded ? 'expanded' : ''}`}
      style={{ '--agent-color': color } as React.CSSProperties}
    >
      {/* Header: Agent name, status indicator */}
      <div className="agent-node__header">
        <StatusIndicator status={status} />
        <span className="agent-node__name">{getAgentDisplayName(agentName)}</span>
        {status === 'completed' && <CheckIcon />}
        {status === 'error' && <WarningIcon />}
      </div>

      {/* Collapsed state: Summary stats */}
      {!expanded && (
        <div className="agent-node__summary">
          <span>{data.claimsCompleted}/{data.claimsAssigned} claims</span>
          <span>{data.findingsCount} findings</span>
        </div>
      )}

      {/* Expanded state: Full content */}
      {expanded && (
        <div className="agent-node__expanded">
          <ReasoningStream reasoning={data.reasoningStream} />
          <FindingsSummary findings={data.findings} />
          {data.agentSpecificContent && (
            <AgentSpecificDisplay
              agentName={agentName}
              content={data.agentSpecificContent}
            />
          )}
        </div>
      )}
    </div>
  );
}
```

### 3.4 Status Indicators

| Status | Visual Indicator | CSS Class |
|---|---|---|
| `idle` | Solid color background, no animation | `agent-node--idle` |
| `working` | Pulsing animation (scale 1.0 → 1.05 → 1.0, 2s cycle) | `agent-node--working` |
| `completed` | Checkmark icon, solid green border | `agent-node--completed` |
| `error` | Warning icon, red border, error message | `agent-node--error` |

### 3.5 Agent Colors

Agent colors are defined as CSS custom properties (from PRD 7.1):

```css
:root {
  --agent-claims: hsl(210, 50%, 50%);        /* Slate blue */
  --agent-orchestrator: hsl(0, 0%, 90%);     /* White/silver */
  --agent-geography: hsl(120, 60%, 30%);     /* Forest green */
  --agent-legal: hsl(270, 60%, 40%);         /* Deep purple */
  --agent-news-media: hsl(45, 90%, 50%);     /* Amber/gold */
  --agent-academic: hsl(180, 50%, 40%);      /* Teal */
  --agent-data-metrics: hsl(15, 80%, 60%);   /* Coral/orange */
  --agent-judge: hsl(0, 70%, 50%);            /* Crimson red */
}
```

### 3.6 Node Styling

```css
.agent-node {
  background: hsl(224, 20%, 14%);
  border: 2px solid var(--agent-color);
  border-radius: 12px;
  padding: 12px;
  min-width: 180px;
  min-height: 80px;
  color: hsl(224, 20%, 85%);
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: all 0.2s ease;
}

.agent-node--working {
  animation: pulse 2s ease-in-out infinite;
}

.agent-node--completed {
  border-color: hsl(120, 60%, 40%);
}

.agent-node--error {
  border-color: hsl(0, 70%, 50%);
}

.agent-node.expanded {
  min-width: 320px;
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}
```

### 3.7 Node Interaction

- **Click to expand:** Clicking a node expands it to show full content.
- **Click outside to collapse:** Clicking the canvas or another node collapses the expanded node.
- **Drag to reposition:** Nodes are draggable for user customization.
- **Hover effects:** Subtle glow effect on hover using the agent color.

---

## 4. Agent-Specific Display Components

### 4.1 Overview

Select agents display domain-specific visual content that would lose meaning if reduced to text-only reasoning. These components are rendered within the expanded `AgentNode` when agent-specific content is available.

### 4.2 Geography Agent: SatelliteImageTile

```typescript
// src/components/Dashboard/AgentSpecific/SatelliteImageTile.tsx

interface SatelliteImageTileProps {
  imageReferences: string[];  // MPC STAC Item URLs
  location: {
    name: string;
    coordinates: [number, number];  // [lat, lon]
  };
  imageryDate: string;
  beforeDate?: string;  // For temporal comparisons
  beforeImageUrl?: string;
}

export function SatelliteImageTile({
  imageReferences,
  location,
  imageryDate,
  beforeDate,
  beforeImageUrl,
}: SatelliteImageTileProps) {
  const [mainImageUrl, setMainImageUrl] = useState<string | null>(null);

  // Fetch signed asset URL from MPC STAC Item
  useEffect(() => {
    if (imageReferences.length > 0) {
      fetchSatelliteImageUrl(imageReferences[0]).then(setMainImageUrl);
    }
  }, [imageReferences]);

  return (
    <div className="satellite-image-tile">
      <div className="satellite-image-tile__image-container">
        {mainImageUrl ? (
          <img
            src={mainImageUrl}
            alt={`Satellite imagery of ${location.name}`}
            className="satellite-image-tile__image"
          />
        ) : (
          <div className="satellite-image-tile__loading">Loading imagery...</div>
        )}
        {beforeImageUrl && (
          <div className="satellite-image-tile__before-after">
            <div className="before-image">
              <img src={beforeImageUrl} alt="Before" />
              <span>{beforeDate}</span>
            </div>
            <div className="after-image">
              <img src={mainImageUrl || ''} alt="After" />
              <span>{imageryDate}</span>
            </div>
          </div>
        )}
      </div>
      <div className="satellite-image-tile__caption">
        <span className="location-name">{location.name}</span>
        <span className="coordinates">
          {location.coordinates[0].toFixed(4)}, {location.coordinates[1].toFixed(4)}
        </span>
        <span className="imagery-date">{imageryDate}</span>
      </div>
    </div>
  );
}
```

**Styling:**
- Image container: `200px × 150px`, rounded corners, border using Geography Agent color
- Caption: Location name, coordinates, date in small text below image
- Before/after comparison: Side-by-side images with date labels

### 4.3 Legal Agent: IFRSCoverageBar

```typescript
// src/components/Dashboard/AgentSpecific/IFRSCoverageBar.tsx

interface IFRSCoverageBarProps {
  coverage: {
    pillar: 'governance' | 'strategy' | 'risk_management' | 'metrics_targets';
    paragraphsCovered: number;
    paragraphsTotal: number;
    paragraphsPartial: number;
    paragraphsGaps: number;
  }[];
}

export function IFRSCoverageBar({ coverage }: IFRSCoverageBarProps) {
  return (
    <div className="ifrs-coverage-bar">
      {coverage.map((pillar) => {
        const coveragePercent = (pillar.paragraphsCovered / pillar.paragraphsTotal) * 100;
        const partialPercent = (pillar.paragraphsPartial / pillar.paragraphsTotal) * 100;
        const gapPercent = (pillar.paragraphsGaps / pillar.paragraphsTotal) * 100;

        return (
          <div key={pillar.pillar} className="ifrs-coverage-bar__pillar">
            <div className="pillar-label">
              {pillar.pillar.replace('_', ' ').toUpperCase()}
            </div>
            <div className="progress-bar">
              <div
                className="progress-segment progress-segment--covered"
                style={{ width: `${coveragePercent}%` }}
              />
              <div
                className="progress-segment progress-segment--partial"
                style={{ width: `${partialPercent}%` }}
              />
              <div
                className="progress-segment progress-segment--gap"
                style={{ width: `${gapPercent}%` }}
              />
            </div>
            <div className="pillar-stats">
              {pillar.paragraphsCovered}/{pillar.paragraphsTotal} covered
              {pillar.paragraphsPartial > 0 && `, ${pillar.paragraphsPartial} partial`}
              {pillar.paragraphsGaps > 0 && `, ${pillar.paragraphsGaps} gaps`}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

**Styling:**
- Progress bar: `100% width`, `8px height`, rounded corners
- Covered segment: `hsl(120, 60%, 40%)` (green)
- Partial segment: `hsl(30, 80%, 50%)` (orange)
- Gap segment: `hsl(224, 20%, 40%)` (grey)
- Pillar label: Small, uppercase, muted color

### 4.4 Data/Metrics Agent: ConsistencyCheckList

```typescript
// src/components/Dashboard/AgentSpecific/ConsistencyCheckList.tsx

interface ConsistencyCheck {
  id: string;
  description: string;
  status: 'pass' | 'fail' | 'pending';
  result?: string;
  details?: string;
}

interface ConsistencyCheckListProps {
  checks: ConsistencyCheck[];
}

export function ConsistencyCheckList({ checks }: ConsistencyCheckListProps) {
  return (
    <div className="consistency-check-list">
      {checks.map((check) => (
        <div
          key={check.id}
          className={`consistency-check consistency-check--${check.status}`}
        >
          <div className="check-indicator">
            {check.status === 'pass' && <CheckIcon className="icon--green" />}
            {check.status === 'fail' && <XIcon className="icon--red" />}
            {check.status === 'pending' && <SpinnerIcon className="icon--muted" />}
          </div>
          <div className="check-content">
            <div className="check-description">{check.description}</div>
            {check.result && (
              <div className="check-result">{check.result}</div>
            )}
            {check.details && (
              <div className="check-details">{check.details}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Styling:**
- Check item: Horizontal layout with icon and text
- Pass: Green checkmark, green text
- Fail: Red X icon, red text, highlighted background
- Pending: Grey spinner, muted text

### 4.5 Judge Agent: VerdictCard

```typescript
// src/components/Dashboard/AgentSpecific/VerdictCard.tsx

interface Verdict {
  claimId: string;
  claimText: string;
  verdict: 'verified' | 'unverified' | 'contradicted' | 'insufficient_evidence';
  cycleCount: number;
  reasoning: string;
}

interface VerdictCardProps {
  verdicts: Verdict[];
}

export function VerdictCard({ verdicts }: VerdictCardProps) {
  return (
    <div className="verdict-card-list">
      {verdicts.map((verdict) => (
        <div
          key={verdict.claimId}
          className={`verdict-card verdict-card--${verdict.verdict}`}
        >
          <div className="verdict-card__header">
            <VerdictBadge verdict={verdict.verdict} />
            {verdict.cycleCount > 1 && (
              <span className="cycle-count">Cycle {verdict.cycleCount}</span>
            )}
          </div>
          <div className="verdict-card__claim">
            {truncateText(verdict.claimText, 100)}
          </div>
          <div className="verdict-card__reasoning">
            {verdict.reasoning}
          </div>
        </div>
      ))}
    </div>
  );
}

function VerdictBadge({ verdict }: { verdict: Verdict['verdict'] }) {
  const config = {
    verified: { label: 'Verified', color: 'hsl(120, 60%, 40%)' },
    unverified: { label: 'Unverified', color: 'hsl(45, 90%, 50%)' },
    contradicted: { label: 'Contradicted', color: 'hsl(0, 70%, 50%)' },
    insufficient_evidence: { label: 'Insufficient Evidence', color: 'hsl(30, 80%, 50%)' },
  }[verdict];

  return (
    <span
      className="verdict-badge"
      style={{ backgroundColor: config.color }}
    >
      {config.label}
    </span>
  );
}
```

**Styling:**
- Verdict card: `100% width`, `120px min-height`, rounded corners, border using verdict color
- Badge: Small pill with verdict label, colored background
- Cycle count: Small badge showing "Cycle N" if > 1
- Scrollable list: Max height `400px`, overflow-y auto

---

## 5. Custom ClaimEdge Component

### 5.1 Overview

The `ClaimEdge` component (`src/components/Dashboard/ClaimEdge.tsx`) is a custom React Flow edge that displays animated particles flowing along the edge to show data movement direction and volume.

### 5.2 Edge Interface

```typescript
interface ClaimEdgeData {
  edgeType: 'claim' | 'reinvestigation' | 'infoRequest';
  claimCount?: number;  // Number of claims/items flowing
  volume: 'low' | 'medium' | 'high';  // Particle density
  direction: 'forward' | 'backward';  // Flow direction
  label?: string;  // Optional edge label
  cycleNumber?: number;  // For reinvestigation edges
}

interface ClaimEdgeProps {
  id: string;
  source: string;
  target: string;
  data: ClaimEdgeData;
  selected: boolean;
  style?: React.CSSProperties;
}
```

### 5.3 Edge Component Structure

```typescript
export function ClaimEdge({
  id,
  source,
  target,
  data,
  selected,
  style,
}: ClaimEdgeProps) {
  const { edgeType, volume, direction, label, cycleNumber } = data;
  const edgePath = useEdgePath(source, target);  // React Flow hook

  return (
    <>
      {/* Base edge line */}
      <path
        id={id}
        d={edgePath}
        className={`claim-edge claim-edge--${edgeType} ${selected ? 'selected' : ''}`}
        strokeWidth={2}
        fill="none"
        style={style}
      />

      {/* Animated particles */}
      <ParticleAnimation
        pathId={id}
        volume={volume}
        direction={direction}
        color={getSourceAgentColor(source)}
      />

      {/* Edge label (if provided) */}
      {label && (
        <EdgeLabel
          pathId={id}
          label={label}
          cycleNumber={cycleNumber}
        />
      )}
    </>
  );
}
```

### 5.4 Particle Animation

```typescript
// src/components/Dashboard/ParticleAnimation.tsx

interface ParticleAnimationProps {
  pathId: string;
  volume: 'low' | 'medium' | 'high';
  direction: 'forward' | 'backward';
  color: string;
}

export function ParticleAnimation({
  pathId,
  volume,
  direction,
  color,
}: ParticleAnimationProps) {
  const particleCount = {
    low: 3,
    medium: 6,
    high: 12,
  }[volume];

  const particles = useMemo(
    () => Array.from({ length: particleCount }, (_, i) => ({
      id: i,
      offset: (i / particleCount) * 100,  // Start position along path (%)
      speed: 0.5 + Math.random() * 0.3,  // Animation speed variation
    })),
    [particleCount]
  );

  return (
    <>
      {particles.map((particle) => (
        <motion.circle
          key={particle.id}
          r={3}
          fill={color}
          opacity={0.8}
          animate={{
            pathLength: direction === 'forward' ? [0, 1] : [1, 0],
            offset: direction === 'forward' 
              ? [particle.offset, 100] 
              : [particle.offset, 0],
          }}
          transition={{
            duration: 2 / particle.speed,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      ))}
    </>
  );
}
```

**Animation details:**
- Particle size: `3px` radius
- Animation duration: `2 seconds` base (varies by particle for natural flow)
- Particle spacing: Evenly distributed along path
- Color: Matches source agent color
- Opacity: `0.8` for visibility without overwhelming the edge

### 5.5 Edge Styling by Type

| Edge Type | Stroke Style | Color | Label |
|---|---|---|---|
| `claim` | Solid | Source agent color | None (or claim count if > 1) |
| `reinvestigation` | Dashed | Judge Agent color (crimson) | "Cycle N" |
| `infoRequest` | Dotted | Orchestrator color (white/silver) | Request type |

### 5.6 Edge Label Component

```typescript
function EdgeLabel({
  pathId,
  label,
  cycleNumber,
}: {
  pathId: string;
  label: string;
  cycleNumber?: number;
}) {
  const [x, y] = useEdgeLabelPosition(pathId);  // Center of edge path

  return (
    <foreignObject x={x - 40} y={y - 10} width={80} height={20}>
      <div className="edge-label">
        {cycleNumber && <span className="cycle-badge">Cycle {cycleNumber}</span>}
        <span>{label}</span>
      </div>
    </foreignObject>
  );
}
```

---

## 6. SSE Event Processing for Graph Updates

### 6.1 Overview

The dashboard derives its state from SSE events streamed from the LangGraph pipeline (FRD 5). The `useDashboard` hook processes incoming events and updates the graph's nodes and edges in real time.

### 6.2 Event Processing Hook

```typescript
// src/hooks/useDashboard.ts

interface UseDashboardReturn {
  nodes: Node[];
  edges: Edge[];
  activeAgents: AgentName[];
  completedAgents: AgentName[];
  erroredAgents: AgentName[];
}

export function useDashboard(
  reportId: string,
  isAnalyzing: boolean,
  events: StreamEvent[]
): UseDashboardReturn {
  const [graphState, setGraphState] = useState<GraphState>(initialGraphState);

  useEffect(() => {
    if (!isAnalyzing && events.length === 0) return;

    // Process each new event
    events.forEach((event) => {
      setGraphState((prev) => processEvent(prev, event));
    });
  }, [events, isAnalyzing]);

  return {
    nodes: graphState.nodes,
    edges: graphState.edges,
    activeAgents: graphState.activeAgents,
    completedAgents: graphState.completedAgents,
    erroredAgents: graphState.erroredAgents,
  };
}
```

### 6.3 Event Processing Logic

```typescript
function processEvent(state: GraphState, event: StreamEvent): GraphState {
  switch (event.event_type) {
    case 'agent_started':
      return {
        ...state,
        nodes: addOrUpdateNode(state.nodes, {
          agentName: event.agent_name!,
          status: 'working',
          claimsAssigned: 0,
          claimsCompleted: 0,
          findingsCount: 0,
          reasoningStream: [],
          findings: [],
          expanded: false,
        }),
        activeAgents: [...state.activeAgents, event.agent_name!],
      };

    case 'agent_thinking':
      return {
        ...state,
        nodes: updateNode(state.nodes, event.agent_name!, (node) => ({
          ...node,
          reasoningStream: [
            ...node.data.reasoningStream.slice(-9),  // Keep last 10 messages
            event.data.message as string,
          ],
        })),
      };

    case 'claim_routed':
      return {
        ...state,
        edges: addClaimEdge(
          state.edges,
          'orchestrator',
          event.data.assigned_agents as AgentName[],
          event.data.claim_id as string
        ),
        nodes: updateNode(state.nodes, 'orchestrator', (node) => ({
          ...node,
          claimsAssigned: node.data.claimsAssigned + 1,
        })),
      };

    case 'evidence_found':
      return {
        ...state,
        nodes: updateNode(state.nodes, event.agent_name!, (node) => {
          const finding = parseFindingFromEvent(event);
          return {
            ...node,
            findingsCount: node.data.findingsCount + 1,
            findings: [...node.data.findings.slice(-9), finding],
            agentSpecificContent: updateAgentSpecificContent(
              node.data.agentSpecificContent,
              event.agent_name!,
              finding
            ),
          };
        }),
        edges: addEvidenceEdge(
          state.edges,
          event.agent_name!,
          'judge',
          event.data.claim_id as string
        ),
      };

    case 'reinvestigation':
      return {
        ...state,
        edges: addReinvestigationEdge(
          state.edges,
          'judge',
          'orchestrator',
          event.data.cycle as number
        ),
      };

    case 'info_request_routed':
      return {
        ...state,
        edges: addInfoRequestEdge(
          state.edges,
          event.data.requesting_agent as AgentName,
          event.data.target_agents as AgentName[],
          event.data.description as string
        ),
      };

    case 'agent_completed':
      return {
        ...state,
        nodes: updateNode(state.nodes, event.agent_name!, (node) => ({
          ...node,
          status: 'completed',
        })),
        activeAgents: state.activeAgents.filter(a => a !== event.agent_name),
        completedAgents: [...state.completedAgents, event.agent_name!],
      };

    case 'error':
      return {
        ...state,
        nodes: updateNode(state.nodes, event.agent_name || 'unknown', (node) => ({
          ...node,
          status: 'error',
        })),
        erroredAgents: [...state.erroredAgents, event.agent_name || 'unknown'],
      };

    default:
      return state;
  }
}
```

### 6.4 Agent-Specific Content Updates

```typescript
function updateAgentSpecificContent(
  current: AgentSpecificContent | undefined,
  agentName: AgentName,
  finding: AgentFinding
): AgentSpecificContent {
  switch (agentName) {
    case 'geography':
      if (finding.details.image_references) {
        return {
          type: 'satellite',
          imageReferences: finding.details.image_references,
          location: finding.details.location,
          imageryDate: finding.details.imagery_dates?.after,
        };
      }
      return current;

    case 'legal':
      return {
        type: 'ifrs_coverage',
        coverage: finding.details.ifrs_coverage || [],
      };

    case 'data_metrics':
      return {
        type: 'consistency_checks',
        checks: finding.details.consistency_checks || [],
      };

    case 'judge':
      return {
        type: 'verdicts',
        verdicts: [
          ...(current?.type === 'verdicts' ? current.verdicts : []),
          {
            claimId: finding.claim_id,
            claimText: finding.summary,
            verdict: finding.supports_claim === true ? 'verified' :
                    finding.supports_claim === false ? 'contradicted' :
                    'unverified',
            cycleCount: finding.iteration || 1,
            reasoning: finding.summary,
          },
        ],
      };

    default:
      return current;
  }
}
```

---

## 7. Node Interaction

### 7.1 Overview

Users can interact with agent nodes by clicking to expand them, revealing detailed content including reasoning streams, findings summaries, and agent-specific displays.

### 7.2 Expansion State Management

```typescript
const [expandedNodeId, setExpandedNodeId] = useState<string | null>(null);

function handleNodeClick(event: React.MouseEvent, node: Node) {
  const nodeId = node.id;
  if (expandedNodeId === nodeId) {
    setExpandedNodeId(null);  // Collapse if already expanded
  } else {
    setExpandedNodeId(nodeId);  // Expand clicked node
  }
}

// Update node data with expansion state
const nodesWithExpansion = nodes.map((node) => ({
  ...node,
  data: {
    ...node.data,
    expanded: expandedNodeId === node.id,
  },
}));
```

### 7.3 Expanded Node Content

When a node is expanded, it displays:

1. **Reasoning Stream:** Scrollable list of recent reasoning messages (last 10-20 messages).
2. **Findings Summary:** Count of findings, recent findings list with summaries.
3. **Claim Count:** "X/Y claims completed" progress indicator.
4. **Agent-Specific Display:** Geography (satellite images), Legal (IFRS bars), Data/Metrics (consistency checks), Judge (verdict cards).

### 7.4 Collapse Behavior

- **Click outside:** Clicking the canvas or another node collapses the expanded node.
- **Escape key:** Pressing Escape collapses the expanded node.
- **Click same node:** Clicking an expanded node collapses it.

### 7.5 Scroll-to-Node

When an agent becomes active (via `agent_started` event), the graph can optionally scroll to that node:

```typescript
const reactFlowInstance = useReactFlow();

useEffect(() => {
  if (newActiveAgent) {
    const node = nodes.find(n => n.data.agentName === newActiveAgent);
    if (node) {
      reactFlowInstance.fitView({
        nodes: [node],
        padding: 0.2,
        duration: 500,
      });
    }
  }
}, [newActiveAgent]);
```

---

## 8. Edge Interaction

### 8.1 Overview

Users can click on edges to see the specific message or data being passed between agents. A popover appears showing claim details, evidence summaries, or request/response content.

### 8.2 Edge Click Handler

```typescript
const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);

function handleEdgeClick(event: React.MouseEvent, edge: Edge) {
  setSelectedEdge(edge);
}

// Render popover for selected edge
{selectedEdge && (
  <EdgePopover
    edge={selectedEdge}
    onClose={() => setSelectedEdge(null)}
  />
)}
```

### 8.3 EdgePopover Component

```typescript
// src/components/Dashboard/EdgePopover.tsx

interface EdgePopoverProps {
  edge: Edge;
  onClose: () => void;
}

export function EdgePopover({ edge, onClose }: EdgePopoverProps) {
  const { data, source, target } = edge;
  const [edgePosition, setEdgePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    // Calculate edge center position for popover placement
    const sourceNode = document.querySelector(`[data-id="${source}"]`);
    const targetNode = document.querySelector(`[data-id="${target}"]`);
    if (sourceNode && targetNode) {
      const sourceRect = sourceNode.getBoundingClientRect();
      const targetRect = targetNode.getBoundingClientRect();
      setEdgePosition({
        x: (sourceRect.right + targetRect.left) / 2,
        y: (sourceRect.top + targetRect.bottom) / 2,
      });
    }
  }, [source, target]);

  return (
    <div
      className="edge-popover"
      style={{
        position: 'absolute',
        left: edgePosition.x,
        top: edgePosition.y,
        transform: 'translate(-50%, -100%)',
      }}
    >
      <div className="edge-popover__header">
        <span>{getAgentDisplayName(source)} → {getAgentDisplayName(target)}</span>
        <button onClick={onClose}>×</button>
      </div>
      <div className="edge-popover__content">
        {data.edgeType === 'claim' && (
          <ClaimEdgeContent claimId={data.claimId} />
        )}
        {data.edgeType === 'reinvestigation' && (
          <ReinvestigationEdgeContent cycleNumber={data.cycleNumber} />
        )}
        {data.edgeType === 'infoRequest' && (
          <InfoRequestEdgeContent request={data.request} />
        )}
      </div>
    </div>
  );
}
```

### 8.4 Edge Content Components

**ClaimEdgeContent:** Shows claim text, IFRS mappings, routing reasoning.

**ReinvestigationEdgeContent:** Shows evidence gap, refined queries, cycle number.

**InfoRequestEdgeContent:** Shows request description, response summary (if available).

---

## 9. Cyclic Validation Visualization

### 9.1 Overview

When the Judge Agent requests re-investigation, a distinct visual representation shows the cyclic loop back to the Orchestrator, highlighting the iterative validation process.

### 9.2 Reinvestigation Edge

The reinvestigation edge uses distinct styling:

- **Stroke style:** Dashed (`strokeDasharray: "8,4"`)
- **Color:** Judge Agent color (crimson red)
- **Label:** "Cycle N" badge
- **Animation:** Pulsing glow effect to draw attention

### 9.3 Cycle Indicator Animation

```css
.reinvestigation-edge {
  stroke: hsl(0, 70%, 50%);
  stroke-dasharray: 8, 4;
  animation: cyclePulse 2s ease-in-out infinite;
}

@keyframes cyclePulse {
  0%, 100% { opacity: 0.6; stroke-width: 2; }
  50% { opacity: 1; stroke-width: 3; }
}
```

### 9.4 Cycle Count Display

The cycle count is displayed as a badge on the edge label:

```typescript
{cycleNumber > 1 && (
  <span className="cycle-badge">
    Cycle {cycleNumber}
  </span>
)}
```

### 9.5 Visual Feedback

When a reinvestigation occurs:

1. The Judge node pulses briefly.
2. The reinvestigation edge appears with animation.
3. The Orchestrator node reactivates (status changes to `working`).
4. A notification message appears: "Re-investigation requested (Cycle N)".

---

## 10. Inter-Agent Communication Visualization

### 10.1 Overview

InfoRequest/Response flows between specialist agents (routed through the Orchestrator) are visualized as distinct edges, separate from claim routing edges.

### 10.2 InfoRequest Edge Structure

InfoRequest edges follow this path:
1. **Requesting agent** → **Orchestrator** (request posted)
2. **Orchestrator** → **Target agent(s)** (request routed)
3. **Target agent** → **Orchestrator** → **Requesting agent** (response)

### 10.3 Edge Styling

| Edge Segment | Style | Color |
|---|---|---|
| Request → Orchestrator | Dotted | Requesting agent color |
| Orchestrator → Target | Dotted | Orchestrator color (white/silver) |
| Response → Requesting | Dotted | Responding agent color |

### 10.4 Edge Label

InfoRequest edges are labeled with the request type:

- "Geographic verification request"
- "Quantitative validation request"
- "Regulatory context request"
- etc.

### 10.5 Interaction

Clicking an InfoRequest edge shows:
- Requesting agent name
- Request description
- Target agent(s)
- Response summary (if available)
- Timestamp

---

## 11. Animation System

### 11.1 Overview

The dashboard uses a comprehensive animation system to provide visual feedback and guide user attention: pulsing nodes for active agents, flowing particles on edges, cycle indicators, and smooth transitions.

### 11.2 Node Animations

| Animation | Trigger | Effect |
|---|---|---|
| **Pulse** | Agent status = `working` | Scale 1.0 → 1.05 → 1.0, 2s cycle |
| **Fade in** | Node appears | Opacity 0 → 1, 300ms |
| **Glow** | Node hover | Box shadow using agent color, 200ms |
| **Expand** | Node expansion | Height/width transition, 300ms ease-out |
| **Checkmark** | Agent completes | Checkmark icon fades in, 400ms |

### 11.3 Edge Animations

| Animation | Trigger | Effect |
|---|---|---|
| **Particle flow** | Edge has data flow | Particles move along path, continuous loop |
| **Fade in** | Edge appears | Opacity 0 → 1, 200ms |
| **Pulse** | Reinvestigation edge | Stroke opacity pulses, 2s cycle |
| **Highlight** | Edge hover/select | Stroke width increases, color brightens |

### 11.4 Transition Timing

| Property | Duration | Easing |
|---|---|---|
| Node expansion | 300ms | `ease-out` |
| Status change | 200ms | `ease-in-out` |
| Edge appearance | 200ms | `ease-in` |
| Particle animation | 2s (base) | `linear` (infinite) |

### 11.5 Performance Considerations

- Use CSS transforms for animations (GPU-accelerated).
- Limit particle count based on edge volume (max 12 particles per edge).
- Debounce rapid status updates to avoid animation jank.
- Use `will-change` CSS property for frequently animated elements.

---

## 12. Analysis Page Center Panel Integration

### 12.1 Overview

The Detective Dashboard replaces the FRD 5 placeholder in the Analysis Page center panel, integrating seamlessly with the three-panel layout.

### 12.2 Panel Integration

```typescript
// src/pages/AnalysisPage.tsx

function AnalysisPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const { isAnalyzing, events } = useSSE(reportId, true);
  const { claims } = useAnalysis(reportId);

  return (
    <AnalysisLayout
      leftPanel={<PDFViewer reportId={reportId} claims={claims} />}
      centerPanel={
        <DashboardGraph
          reportId={reportId}
          isAnalyzing={isAnalyzing}
          events={events}
        />
      }
      rightPanel={<AgentReasoningPanel reportId={reportId} events={events} />}
    />
  );
}
```

### 12.3 Panel Header

The center panel header displays:

- **Title:** "Investigation Dashboard"
- **Status indicator:** Shows current pipeline stage (extracting, routing, investigating, judging, completed)
- **Agent count:** "X agents active"

### 12.4 Responsive Behavior

- **Wide panels:** Full graph layout with all features.
- **Medium panels:** Compact node sizes, reduced spacing.
- **Narrow panels:** Hide minimap, reduce controls, stack nodes vertically if needed.

### 12.5 Panel Resizing

The dashboard adapts to panel width changes:

- Recalculates node positions on resize.
- Adjusts zoom level to fit content.
- Maintains user's pan position (if possible).

---

## 13. State Management

### 13.1 Overview

The dashboard state is derived from SSE events and managed via the `useDashboard` hook, which processes events and maintains the graph's nodes and edges.

### 13.2 Graph State Structure

```typescript
interface GraphState {
  nodes: Node<AgentNodeData>[];
  edges: Edge<ClaimEdgeData>[];
  activeAgents: AgentName[];
  completedAgents: AgentName[];
  erroredAgents: AgentName[];
  expandedNodeId: string | null;
  selectedEdgeId: string | null;
  lastEventTimestamp: string;
}
```

### 13.3 State Initialization

```typescript
const initialGraphState: GraphState = {
  nodes: [
    {
      id: 'claims',
      type: 'agent',
      position: { x: 400, y: 50 },
      data: {
        agentName: 'claims',
        status: 'idle',
        claimsAssigned: 0,
        claimsCompleted: 0,
        findingsCount: 0,
        reasoningStream: [],
        findings: [],
        expanded: false,
      },
    },
    {
      id: 'orchestrator',
      type: 'agent',
      position: { x: 400, y: 200 },
      data: {
        agentName: 'orchestrator',
        status: 'idle',
        // ... similar structure
      },
    },
  ],
  edges: [],
  activeAgents: [],
  completedAgents: [],
  erroredAgents: [],
  expandedNodeId: null,
  selectedEdgeId: null,
  lastEventTimestamp: '',
};
```

### 13.4 State Updates

State updates are performed immutably:

```typescript
function updateNode(
  nodes: Node[],
  agentName: AgentName,
  updater: (node: Node) => Node
): Node[] {
  return nodes.map((node) =>
    node.data.agentName === agentName ? updater(node) : node
  );
}
```

### 13.5 State Persistence

For completed analyses, the graph state can be persisted:

- Store final node/edge state in React state or localStorage.
- Replay events on page reload for completed analyses.
- Enable "replay" mode to step through the investigation chronologically.

---

## 14. Performance Optimization

### 14.1 Overview

The dashboard must handle large graphs (100+ claims, 8 agents, many edges) while maintaining smooth 60fps interactions. Performance optimizations include React Flow memoization, virtualization, and efficient event processing.

### 14.2 React Flow Memoization

```typescript
// Memoize node components
const AgentNodeMemo = React.memo(AgentNode, (prev, next) => {
  return (
    prev.data.status === next.data.status &&
    prev.data.expanded === next.data.expanded &&
    prev.data.findingsCount === next.data.findingsCount &&
    prev.selected === next.selected
  );
});

// Memoize edge components
const ClaimEdgeMemo = React.memo(ClaimEdge, (prev, next) => {
  return (
    prev.data.volume === next.data.volume &&
    prev.data.direction === next.data.direction &&
    prev.selected === next.selected
  );
});
```

### 14.3 Event Processing Optimization

- **Batch updates:** Process multiple events in a single state update when possible.
- **Debounce rapid events:** If events arrive faster than 60fps, batch them.
- **Filter irrelevant events:** Skip events that don't affect the graph visualization.

### 14.4 Particle Animation Optimization

- **Limit particle count:** Max 12 particles per edge, reduce for low-volume edges.
- **Use CSS animations:** Prefer CSS `@keyframes` over JavaScript animations for particles.
- **Pause off-screen animations:** Stop particle animations for edges outside the viewport.

### 14.5 Virtualization

For large graphs:

- Render only nodes/edges within the viewport (React Flow handles this internally).
- Lazy-load agent-specific content (satellite images, IFRS data) when nodes expand.
- Virtualize long lists (verdict cards, consistency checks) within expanded nodes.

### 14.6 Rendering Optimization

- Use `React.memo` for expensive components.
- Avoid unnecessary re-renders with proper dependency arrays.
- Use `useMemo` for computed values (node positions, edge paths).

---

## 15. Error and Edge Case Handling

### 15.1 Overview

The dashboard handles errors gracefully: missing events, agent failures, network disconnections, and edge cases like empty graphs or malformed data.

### 15.2 Missing Events

| Scenario | Handling |
|---|---|
| Event arrives out of order | Sort events by timestamp before processing |
| Missing `agent_started` event | Infer agent activation from first `agent_thinking` event |
| Missing `agent_completed` event | Mark agent as completed when Judge starts (for specialists) |

### 15.3 Agent Failures

| Scenario | Handling |
|---|---|
| Agent status = `error` | Display error icon, show error message in expanded node |
| Agent never completes | Show "Timeout" status after 5 minutes of inactivity |
| Agent produces no findings | Show "0 findings" in summary, no error state |

### 15.4 Network Disconnections

| Scenario | Handling |
|---|---|
| SSE connection lost | Show "Reconnecting..." indicator, auto-reconnect |
| Events missed during disconnect | Fetch missed events via `GET /api/v1/analysis/{reportId}/events` |
| Reconnection successful | Resume graph updates from last received event |

### 15.5 Empty Graph

If no events have been received:

- Show placeholder message: "Waiting for analysis to start..."
- Display loading skeleton for expected nodes.
- Provide "Start Analysis" button if analysis hasn't begun.

### 15.6 Malformed Data

| Scenario | Handling |
|---|---|
| Invalid agent name in event | Skip event, log warning |
| Missing required fields | Use defaults (status = 'idle', empty arrays) |
| Invalid node position | Use default layout coordinates |

### 15.7 Performance Degradation

If the graph becomes too large (>200 nodes/edges):

- Show warning: "Graph is large. Some features may be slower."
- Offer "Simplify view" option (hide completed agents, collapse edges).
- Enable "Minimal mode" (nodes only, no particles, no animations).

---

## 16. Exit Criteria

FRD 12 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | React Flow graph renders in center panel | Navigate to `/analysis/{reportId}`; verify graph is visible |
| 2 | Agent nodes are positioned correctly | Verify Claims (top), Orchestrator (middle-top), specialists (row), Judge (bottom) |
| 3 | Agent nodes display correct colors | Verify each agent uses its unique color from PRD 7.1 |
| 4 | Status indicators work | Verify pulsing (active), solid (idle), checkmark (complete), warning (error) |
| 5 | Nodes expand on click | Click an agent node; verify it expands to show content |
| 6 | Expanded nodes show reasoning stream | Verify recent reasoning messages are displayed |
| 7 | Expanded nodes show findings summary | Verify findings count and recent findings are shown |
| 8 | Geography Agent shows satellite images | Expand Geography node; verify satellite image tile appears |
| 9 | Legal Agent shows IFRS progress bars | Expand Legal node; verify progress bars per pillar (green/orange/grey) |
| 10 | Data/Metrics Agent shows consistency checks | Expand Data/Metrics node; verify check list with pass/fail indicators |
| 11 | Judge Agent shows verdict cards | Expand Judge node; verify verdict cards with color-coded badges |
| 12 | Edges display animated particles | Verify particles flow along edges showing data direction |
| 13 | Particle density reflects volume | Verify more particles for high-volume edges |
| 14 | Edges are clickable | Click an edge; verify popover appears with claim/evidence details |
| 15 | Reinvestigation edges are distinct | Trigger re-investigation; verify dashed edge from Judge to Orchestrator |
| 16 | Cycle count displays on reinvestigation | Verify "Cycle N" badge appears on reinvestigation edges |
| 17 | InfoRequest edges are visible | Trigger inter-agent communication; verify dotted edges through Orchestrator |
| 18 | Graph updates in real time | Start analysis; verify nodes/edges appear as events stream |
| 19 | Updates occur within 500ms | Measure time from event emission to graph update |
| 20 | Graph remains interactive during updates | Verify zoom/pan/click work while graph is updating |
| 21 | Layout handles many claims | Test with 100+ claims; verify layout remains readable |
| 22 | Performance is smooth (60fps) | Verify no jank during interactions, animations run smoothly |
| 23 | Panel resizing works | Resize center panel; verify graph adapts correctly |
| 24 | Error handling works | Simulate agent error; verify error icon and message appear |
| 25 | SSE reconnection works | Disconnect network; verify reconnection and event catch-up |
| 26 | Empty state displays correctly | Load page before analysis starts; verify placeholder message |
| 27 | Minimap shows correct colors | Verify minimap nodes use agent colors |
| 28 | Zoom/pan controls work | Use React Flow controls; verify zoom in/out, pan, fit view |
| 29 | Graph state persists for completed analyses | Reload page after analysis completes; verify graph state is restored |
| 30 | Integration with Analysis Page works | Verify dashboard integrates seamlessly with left (PDF) and right (reasoning) panels |

---

## Appendix A: Agent Color Palette Reference

| Agent | Color Name | HSL Value | RGB Value | Usage |
|---|---|---|---|---|
| Claims | Slate blue | `hsl(210, 50%, 50%)` | `rgb(64, 115, 191)` | Node border, particles, highlights |
| Orchestrator | White/silver | `hsl(0, 0%, 90%)` | `rgb(230, 230, 230)` | Node border, InfoRequest edges |
| Geography | Forest green | `hsl(120, 60%, 30%)` | `rgb(31, 122, 31)` | Node border, particles, satellite tile border |
| Legal | Deep purple | `hsl(270, 60%, 40%)` | `rgb(102, 41, 163)` | Node border, particles, IFRS bar accents |
| News/Media | Amber/gold | `hsl(45, 90%, 50%)` | `rgb(255, 204, 0)` | Node border, particles |
| Academic | Teal | `hsl(180, 50%, 40%)` | `rgb(51, 153, 153)` | Node border, particles |
| Data/Metrics | Coral/orange | `hsl(15, 80%, 60%)` | `rgb(255, 127, 80)` | Node border, particles, consistency check accents |
| Judge | Crimson red | `hsl(0, 70%, 50%)` | `rgb(191, 38, 38)` | Node border, particles, reinvestigation edges |

---

## Appendix B: Graph Layout Coordinates

### B.1 Default Coordinates (800px × 600px canvas)

| Agent | X | Y | Notes |
|---|---|---|---|
| Claims | 400 | 50 | Top center |
| Orchestrator | 400 | 200 | Below Claims |
| Geography | 200 | 400 | Left specialist |
| Legal | 300 | 400 | Second left |
| News/Media | 400 | 400 | Center specialist |
| Academic | 500 | 400 | Second right |
| Data/Metrics | 600 | 400 | Right specialist |
| Judge | 400 | 600 | Bottom center |

### B.2 Coordinate Calculation

```typescript
const LAYOUT_CONFIG = {
  claimsY: 50,
  orchestratorY: 200,
  specialistsY: 400,
  judgeY: 600,
  nodeSpacing: 100,
  centerX: 400,
};

function calculateSpecialistPositions(activeSpecialists: AgentName[]): Map<AgentName, { x: number; y: number }> {
  const positions = new Map();
  const count = activeSpecialists.length;
  const totalWidth = (count - 1) * LAYOUT_CONFIG.nodeSpacing;
  const startX = LAYOUT_CONFIG.centerX - totalWidth / 2;

  activeSpecialists.forEach((agent, index) => {
    positions.set(agent, {
      x: startX + index * LAYOUT_CONFIG.nodeSpacing,
      y: LAYOUT_CONFIG.specialistsY,
    });
  });

  return positions;
}
```

---

## Appendix C: SSE Event to Graph Update Mapping

| SSE Event Type | Graph Update | Details |
|---|---|---|
| `agent_started` | Add/update node | Set status = 'working', add to activeAgents |
| `agent_thinking` | Update node | Append message to reasoningStream |
| `claim_routed` | Add edge | Create edge Orchestrator → target agents, update Orchestrator claimsAssigned |
| `evidence_found` | Update node, add edge | Update agent findingsCount, add edge agent → Judge |
| `reinvestigation` | Add edge | Create dashed edge Judge → Orchestrator with cycle number |
| `info_request_routed` | Add edges | Create dotted edges requesting → Orchestrator → target |
| `info_response_posted` | Add edge | Create dotted edge responding → requesting |
| `agent_completed` | Update node | Set status = 'completed', move to completedAgents |
| `error` | Update node | Set status = 'error', add to erroredAgents |
| `pipeline_completed` | Update all nodes | Mark all active agents as completed |

---

## Appendix D: Animation Specifications

### D.1 Node Pulse Animation

```css
@keyframes nodePulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
    box-shadow: 0 4px 16px var(--agent-color);
  }
}

.agent-node--working {
  animation: nodePulse 2s ease-in-out infinite;
}
```

### D.2 Particle Flow Animation

```css
@keyframes particleFlow {
  0% {
    offset-distance: 0%;
    opacity: 0;
  }
  10% {
    opacity: 0.8;
  }
  90% {
    opacity: 0.8;
  }
  100% {
    offset-distance: 100%;
    opacity: 0;
  }
}

.particle {
  animation: particleFlow 2s linear infinite;
  r: 3;
  fill: var(--particle-color);
}
```

### D.3 Reinvestigation Edge Pulse

```css
@keyframes cyclePulse {
  0%, 100% {
    opacity: 0.6;
    stroke-width: 2;
  }
  50% {
    opacity: 1;
    stroke-width: 3;
  }
}

.reinvestigation-edge {
  animation: cyclePulse 2s ease-in-out infinite;
}
```

### D.4 Node Expansion Transition

```css
.agent-node {
  transition: min-width 0.3s ease-out,
              min-height 0.3s ease-out,
              max-height 0.3s ease-out;
}

.agent-node.expanded {
  min-width: 320px;
  min-height: 400px;
  max-height: 600px;
}
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| React Flow (`@xyflow/react`) over D3.js or custom canvas | React Flow provides built-in zoom/pan, node/edge interactions, and React integration. D3.js would require custom implementation of these features. Custom canvas would require even more work. React Flow is the most efficient choice for MVP. |
| Custom node/edge components over default React Flow nodes | Default nodes are generic rectangles. Custom components enable agent-specific displays (satellite images, IFRS bars, verdict cards) and status indicators (pulsing, checkmarks) that are essential for the detective dashboard's visual impact. |
| Percentage-based particle animation over absolute positioning | Particles follow edge paths dynamically. Percentage-based animation (0% to 100% along path) adapts to any edge shape/length. Absolute positioning would break with curved or diagonal edges. |
| Agent-specific displays only for Geography, Legal, Data/Metrics, Judge | These agents produce visual data (images, progress bars, checks, verdicts) that benefit from visual representation. Other agents (Claims, Orchestrator, News/Media, Academic) produce text-only findings that are adequately displayed in reasoning streams. |
| Expandable nodes over always-expanded | Always-expanded nodes would create visual clutter and make the graph unreadable. Expandable nodes keep the graph compact while allowing detailed inspection on demand. |
| Click-to-expand over hover-to-expand | Click provides explicit user intent and prevents accidental expansions. Hover would cause nodes to expand/unexpand as the mouse moves, creating a distracting experience. |
| Separate edge types for claim/reinvestigation/infoRequest | Different edge types enable distinct styling (solid/dashed/dotted) and behavior. A single edge type with data properties would require complex conditional styling logic. Separate types are cleaner. |
| Particle animation on all edges over static edges | Animated particles provide immediate visual feedback about data flow direction and volume. Static edges would make the graph feel lifeless. Particles are lightweight (CSS animations) and enhance UX significantly. |
| Real-time updates from SSE over polling | SSE provides immediate updates (<500ms latency) and reduces server load compared to polling. Polling would introduce delays and unnecessary API calls. SSE is the right choice for real-time visualization. |
| Graph state derived from events over separate API endpoint | Deriving state from events ensures consistency with the actual pipeline execution. A separate API endpoint might return stale or inconsistent data. Event-driven state is the source of truth. |
| Memoization of node/edge components | Large graphs (100+ edges) would cause performance issues without memoization. Memoization prevents unnecessary re-renders when unrelated nodes update. Essential for smooth 60fps performance. |
| Minimap with agent colors over default minimap | Agent-colored minimap provides quick visual reference for node locations. Default minimap (single color) would be less informative. The color coding helps users navigate large graphs. |
| Cycle count badge on reinvestigation edges | Cycle count provides critical context about how many re-investigation loops have occurred. Without it, users can't distinguish Cycle 1 from Cycle 3. Essential for understanding the validation process. |
| Satellite image tile in Geography node over external link | Embedded image tile provides immediate visual context without leaving the dashboard. External links would break the immersive experience. The tile is small enough (200×150px) to not overwhelm the node. |
| IFRS progress bars per pillar over single aggregate | Per-pillar breakdown shows which IFRS areas are well-covered vs. gaps. A single aggregate bar would hide important detail. Four bars (Governance, Strategy, Risk Management, Metrics) provide actionable insight. |
| Consistency check list in Data/Metrics node over summary count | The list shows which specific checks passed/failed, enabling users to understand quantitative validation results. A summary count ("5 checks passed, 2 failed") would hide the details. The list is scrollable if long. |
| Verdict cards in Judge node over simple list | Cards provide visual hierarchy with color-coded badges and cycle counts. A simple text list would be harder to scan. Cards make verdicts immediately recognizable (green=verified, red=contradicted). |
| Panel resizing support | Users may want more space for the dashboard or other panels. Resizing enables customization. The graph adapts by recalculating layout and adjusting zoom. Essential for flexible UX. |
| Error state in nodes over hiding failed agents | Error state (warning icon, red border) makes agent failures visible and auditable. Hiding failed agents would obscure problems. Transparency is a core value of the detective dashboard. |
| SSE reconnection with event catch-up | Network disconnections are inevitable. Reconnection ensures the graph eventually reflects the full investigation. Event catch-up (fetching missed events) prevents gaps in the visualization. |
| Graph state persistence for completed analyses | Users may reload the page after analysis completes. Persisting state (or replaying events) ensures the graph is still viewable. Without persistence, the graph would be empty on reload. |

---

*This FRD establishes the complete specification for the Detective Dashboard, enabling users to watch the full multi-agent investigation unfold in real time through an animated, interactive network graph visualization.*
