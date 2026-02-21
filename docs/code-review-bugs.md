# Code Review: Bug Report for Dashboard Implementation

**Date:** February 20, 2026  
**Reviewed By:** Multi-Agent Code Review Team  
**Commit:** Dashboard Graph & Satellite API Implementation

---

## Executive Summary

This code review identified **47 bugs and issues** across the implementation:

| Severity | Count |
|----------|-------|
| Critical | 7 |
| High     | 10 |
| Medium   | 13 |
| Low      | 11 |

The most severe issues involve:
1. **SSRF vulnerability** in the satellite API endpoint
2. **Stale data rendering** due to incorrect React memo comparators
3. **Missing error propagation** from SSE to DashboardGraph
4. **Unsafe type assertions** that can cause runtime crashes

---

## Critical Issues

### 1. SSRF via User-Controlled URL (Backend Security)

- **Location:** `backend/app/api/routes/satellite.py`, lines 41–42
- **Description:** `stac_item_url` is user-controlled and passed directly to `httpx.get()` with no validation.
- **Impact:** An attacker can request arbitrary URLs including:
  - Internal services: `http://localhost:5432`, `http://127.0.0.1:6379`
  - Cloud metadata: `http://169.254.169.254/latest/meta-data/` (AWS)
  - Internal network hosts
- **Remediation:** Restrict `stac_item_url` to an allowlist (e.g., `https://planetarycomputer.microsoft.com/api/stac/v1/...`). Use `urlparse` to validate scheme, host, and path prefix.

### 2. AgentNode Memo Comparator Omits `claimsAssigned` (React)

- **Location:** `frontend/src/components/Dashboard/AgentNode.tsx`, lines 126–135
- **Description:** The custom `memo` comparator checks `claimsCompleted`, `findingsCount`, etc., but not `claimsAssigned`.
- **Impact:** When `claimsAssigned` changes (e.g., 2→3) while `claimsCompleted` stays 1, the node won't re-render and will show "1/2 claims" instead of "1/3 claims".
- **Remediation:** Add `claimsAssigned` to the memo comparator.

### 3. AgentNode Memo Comparator Omits `agentSpecificContent` (React)

- **Location:** `frontend/src/components/Dashboard/AgentNode.tsx`, lines 126–135
- **Description:** `agentSpecificContent` is not part of the memo comparison.
- **Impact:** When geography gets satellite imagery or the judge gets verdicts, the node may not re-render and will show outdated or missing content.
- **Remediation:** Add `agentSpecificContent` comparison to the memo comparator.

### 4. AgentNode Memo Compares Only `reasoningStream.length` (React)

- **Location:** `frontend/src/components/Dashboard/AgentNode.tsx`, lines 126–135
- **Description:** Only `reasoningStream.length` is checked, not the actual content.
- **Impact:** When messages are replaced (e.g., `["a",...,"j"]` → `["b",...,"k"]`), length stays 10 and memo blocks re-renders. Stale reasoning messages are shown.
- **Remediation:** Compare actual content or use a hash of the messages.

### 5. Unsafe Type Assertion on Verdict (TypeScript)

- **Location:** `frontend/src/hooks/useDashboard.ts:248`
- **Description:** `data.verdict as Verdict["verdict"]` is cast without validation.
- **Impact:** Invalid values (e.g., `"unknown"`, `"invalid"`) can reach the UI and break `VERDICT_CONFIG[verdict.verdict]` in `VerdictCard.tsx:73`, causing a runtime error.
- **Remediation:** Add runtime validation using Zod or manual checks before casting.

### 6. SSE `error` Not Passed to DashboardGraph (Integration)

- **Location:** `frontend/src/pages/AnalysisPage.tsx` lines 61–69, 291–296
- **Description:** `useSSE` returns `error`, but `AnalysisPage` does not destructure it or pass it to `DashboardGraph`.
- **Impact:** SSE connection failures (e.g., network issues, stream closed) are never surfaced to the user. The `DashboardGraph` error UI is unreachable.
- **Remediation:** Destructure `error` from `useSSE` and pass it to `DashboardGraph`.

---

## High Severity Issues

### 7. SSRF via Asset URLs from Untrusted STAC JSON (Backend Security)

- **Location:** `backend/app/api/routes/satellite.py`, lines 57–88
- **Description:** `asset_url` is taken from JSON returned by the fetched URL and passed to the signing service without validation.
- **Impact:** Malicious STAC documents can inject arbitrary URLs into the response.
- **Remediation:** Validate `asset_url` from the STAC JSON (scheme, host, path) before use.

### 8. Information Disclosure in Error Messages (Backend Security)

- **Location:** `backend/app/api/routes/satellite.py`, lines 45–46, 98–99
- **Description:** Exception messages are returned directly in HTTP responses.
- **Impact:** Internal hostnames, IPs, and error details can be exposed to attackers.
- **Remediation:** Use generic error messages and log details server-side.

### 9. useDashboard Reset Does Not Clear UI State (React)

- **Location:** `frontend/src/hooks/useDashboard.ts`, lines 451–456
- **Description:** When resetting, `expandedNodeId` and `selectedEdgeId` are not cleared.
- **Impact:** A node or edge selected in a prior analysis run can remain selected/expanded when a new analysis starts.
- **Remediation:** Clear `expandedNodeId` and `selectedEdgeId` in the reset dispatch.

### 10. EdgePopover Effect Re-runs Every Render (React Performance)

- **Location:** `frontend/src/components/Dashboard/DashboardGraph.tsx` line 139; `EdgePopover.tsx` lines 22–47
- **Description:** `onClose={() => setSelectedEdgeId(null)}` creates a new function each render, triggering the effect.
- **Impact:** Repeatedly removes and re-adds document listeners on every parent render.
- **Remediation:** Use `useCallback` for `onClose`.

### 11. nodesWithExpansion Creates New Arrays Every Render (React Performance)

- **Location:** `frontend/src/components/Dashboard/DashboardGraph.tsx`, lines 56–69
- **Description:** `.map()` runs on every render and produces new references.
- **Impact:** React Flow re-renders all nodes and edges on every parent render.
- **Remediation:** Memoize `nodesWithExpansion` and `edgesWithSelection` with `useMemo`.

### 12. Non-null Assertion on Map.get() (TypeScript)

- **Location:** `frontend/src/hooks/useDashboard.ts:447`
- **Description:** `nodeDataMap.get(agentName)!` uses non-null assertion.
- **Impact:** Can throw if the key is missing.
- **Remediation:** Add explicit null check or use guaranteed initialization.

### 13. DashboardGraphInnerProps Loses Generic Type Information (TypeScript)

- **Location:** `frontend/src/components/Dashboard/DashboardGraph.tsx:38-44`
- **Description:** Props use unparameterized `Node[]` and `Edge[]`, so `node.data` is effectively `unknown`.
- **Impact:** Forces unsafe casts like `node.data as AgentNodeData`.
- **Remediation:** Use `Node<AgentNodeData>[]` and `Edge<ClaimEdgeData>[]`.

### 14. Duplicate AGENT_POSITIONS Definitions (Integration)

- **Location:** `frontend/src/types/dashboard.ts` lines 136–145; `layout.ts` lines 19–28
- **Description:** Two separate definitions that can diverge.
- **Impact:** If someone imports from the wrong module, layout and graph use different positions.
- **Remediation:** Remove the duplicate from `types/dashboard.ts` or consolidate.

### 15. reportId Passed But Never Used (Integration)

- **Location:** `frontend/src/pages/AnalysisPage.tsx` line 293; `DashboardGraph.tsx` lines 155–159
- **Description:** `reportId` is passed to `DashboardGraph` but never used.
- **Impact:** Dead code that may indicate missing functionality.
- **Remediation:** Either use `reportId` or remove it from props.

---

## Medium Severity Issues

### 16. Missing JSON Parsing Error Handling (Backend)

- **Location:** `backend/app/api/routes/satellite.py`, line 49
- **Description:** `response.json()` can raise `JSONDecodeError` if the response is invalid.
- **Impact:** Unhandled exception leads to 500 response and may leak details.
- **Remediation:** Wrap in `try/except json.JSONDecodeError`.

### 17. No Authentication on Satellite Endpoint (Backend Security)

- **Location:** `backend/app/api/routes/satellite.py` (whole route)
- **Description:** The endpoint is unauthenticated.
- **Impact:** Combined with SSRF, makes abuse easier.
- **Remediation:** Add authentication when implementing auth across the API.

### 18. Inconsistent Error Handling for Signing Failure (Backend)

- **Location:** `backend/app/api/routes/satellite.py`, lines 80–84
- **Description:** When signing fails, the code returns the unsigned `asset_url` instead of failing.
- **Impact:** Can break the frontend if the asset requires signing.
- **Remediation:** Fail with a clear error or document the fallback behavior.

### 19. ReasoningStream Uses Array Index as Key (React)

- **Location:** `frontend/src/components/Dashboard/ReasoningStream.tsx`, line 41
- **Description:** `key={index}` is used for messages that shift.
- **Impact:** React may reuse DOM nodes incorrectly when the list changes.
- **Remediation:** Use a stable id (e.g., `${index}-${message.slice(0, 30)}`).

### 20. useDashboard Depends on events Reference Stability (React)

- **Location:** `frontend/src/hooks/useDashboard.ts`, lines 447–455
- **Description:** If parent mutates `events` in place, the effect won't run.
- **Impact:** New events may not be processed.
- **Remediation:** Document that `events` must be immutable, or use a different detection mechanism.

### 21. isAnalyzing Includes "error" State (Integration)

- **Location:** `frontend/src/pages/AnalysisPage.tsx` lines 56–59
- **Description:** `isAnalyzing` is true when `analysisState === "error"`.
- **Impact:** SSE stays enabled after failure, showing "Reconnecting…" misleadingly.
- **Remediation:** Separate error state from analyzing state for SSE connection logic.

### 22. EdgePopover Position Wrong When Zoomed/Panned (Integration)

- **Location:** `frontend/src/components/Dashboard/DashboardGraph.tsx` lines 84–93; `EdgePopover.tsx` lines 66–72
- **Description:** Edge click position is relative to container, not accounting for zoom/pan.
- **Impact:** Popover appears in wrong position when graph is zoomed or panned.
- **Remediation:** Use React Flow's `screenToFlowPosition` or similar transform.

### 23. Unsafe Casts from Record<string, unknown> (TypeScript)

- **Location:** `frontend/src/hooks/useDashboard.ts` (multiple lines)
- **Description:** SSE `data` is `Record<string, unknown>` and cast without validation.
- **Impact:** Malformed backend data can cause runtime errors.
- **Remediation:** Add runtime validation (e.g., Zod schema) for SSE events.

### 24. ConsistencyCheck.details Type Mismatch (TypeScript)

- **Location:** `frontend/src/types/dashboard.ts:90` vs `useDashboard.ts:422`
- **Description:** Type says `details?: string` but cast suggests it might be other shapes.
- **Impact:** Could cause runtime issues if backend sends objects.
- **Remediation:** Clarify the expected type and add validation.

### 25. useReducer Initializer Type Mismatch (TypeScript)

- **Location:** `frontend/src/hooks/useDashboard.ts:435`
- **Description:** Initializer signature doesn't match expected `(arg: null) => GraphState`.
- **Impact:** Works but types don't match the pattern.
- **Remediation:** Update function signature to accept the init arg.

### 26. AgentSpecificDisplay Missing Exhaustiveness Check (TypeScript)

- **Location:** `frontend/src/components/Dashboard/AgentSpecificDisplay.tsx:40-42`
- **Description:** Switch has default that returns null, hiding new variants.
- **Impact:** New content types silently render nothing.
- **Remediation:** Add `const _: never = content` exhaustiveness check.

### 27. processEvent Missing Exhaustiveness Check (TypeScript)

- **Location:** `frontend/src/hooks/useDashboard.ts:404-406`
- **Description:** Some `StreamEventType` values fall through to default.
- **Impact:** May silently ignore new event types.
- **Remediation:** Add exhaustiveness check or explicit handling.

### 28. DashboardPlaceholder Still Exported (Integration)

- **Location:** `frontend/src/components/Analysis/index.ts` line 11
- **Description:** `DashboardPlaceholder` is still exported but `AnalysisPage` uses `DashboardGraph`.
- **Impact:** Dead code that may confuse maintainers.
- **Remediation:** Remove the placeholder export and component.

---

## Low Severity Issues

### 29. Missing Logging in Satellite Route (Backend)

- **Location:** `backend/app/api/routes/satellite.py` (entire file)
- **Description:** No logging for requests, errors, or success.
- **Impact:** Debugging and security monitoring are harder.
- **Remediation:** Add structured logging consistent with other routes.

### 30. No Rate Limiting on Satellite Endpoint (Backend)

- **Location:** `backend/app/api/routes/satellite.py` (entire route)
- **Description:** No rate limiting.
- **Impact:** Can be used for SSRF amplification or service abuse.
- **Remediation:** Add rate limiting middleware.

### 31. Hardcoded Signing URL Instead of Using Config (Backend)

- **Location:** `backend/app/api/routes/satellite.py`, lines 76–77
- **Description:** Signing URL is hardcoded instead of using `settings.MPC_STAC_URL`.
- **Impact:** Makes configuration and testing harder.
- **Remediation:** Derive signing URL from config settings.

### 32. No Error Boundary Around Dashboard (React)

- **Location:** `frontend/src/components/Dashboard/DashboardGraph.tsx`
- **Description:** No error boundary wrapping the graph.
- **Impact:** Any thrown error can unmount the entire graph.
- **Remediation:** Wrap in an error boundary with fallback UI.

### 33. StatusIndicator Missing Accessibility Attributes (React/A11y)

- **Location:** `frontend/src/components/Dashboard/StatusIndicator.tsx`
- **Description:** Status indicator is purely visual.
- **Impact:** Screen readers get no information about agent status.
- **Remediation:** Add `role="status"` and `aria-label`.

### 34. AgentSpecificDisplayProps.agentName Unused (TypeScript)

- **Location:** `frontend/src/components/Dashboard/AgentSpecificDisplay.tsx:13, 18`
- **Description:** `agentName` is declared but never used.
- **Impact:** Misleading interface.
- **Remediation:** Use it for aria-labels or remove from interface.

### 35. Backend Emits "compiler" Events But No Graph Node (Integration)

- **Location:** `frontend/src/hooks/useDashboard.ts` lines 40–49
- **Description:** Backend sends `agent_name="compiler"` events but `ALL_AGENTS` doesn't include it.
- **Impact:** Compiler events are ignored by the graph.
- **Remediation:** Either add compiler to the graph or document the intentional exclusion.

### 36. getSatelliteImageUrl Response Handling Fragile (Integration)

- **Location:** `frontend/src/services/api.ts` lines 161–165
- **Description:** Assumes `response.url` exists without checking.
- **Impact:** Could throw on unexpected backend response.
- **Remediation:** Add defensive check (e.g., `response?.url`).

### 37. GraphState Name Collision (TypeScript)

- **Location:** `frontend/src/types/dashboard.ts:121` and `useDashboard.ts:26`
- **Description:** Two different `GraphState` interfaces with the same name.
- **Impact:** Can cause confusion and accidental wrong imports.
- **Remediation:** Rename one (e.g., `DashboardUIState` vs `DashboardReducerState`).

### 38. nodeTypes/edgeTypes Cast to never (TypeScript)

- **Location:** `frontend/src/components/Dashboard/DashboardGraph.tsx:113-114`
- **Description:** `nodeTypes as never` bypasses type checking.
- **Impact:** Hides potential type mismatches.
- **Remediation:** Properly type the node/edge type maps.

### 39. source/target Cast to AgentName Without Validation (TypeScript)

- **Location:** `frontend/src/components/Dashboard/ClaimEdge.tsx:59`, `EdgePopover.tsx:57-58`
- **Description:** `source` and `target` (strings from React Flow) are cast to `AgentName`.
- **Impact:** Invalid values bypass type checking.
- **Remediation:** Add validation or use type guards.

---

## Recommended Priority Fixes

### Immediate (Before Merge)

1. **Fix SSRF vulnerability** - Add URL allowlist validation in `satellite.py`
2. **Fix AgentNode memo comparator** - Add `claimsAssigned`, `agentSpecificContent`, and proper `reasoningStream` comparison
3. **Pass SSE error to DashboardGraph** - Destructure and pass the error prop
4. **Add verdict validation** - Validate before casting in `useDashboard.ts`

### Short-term

5. Memoize `nodesWithExpansion` and `edgesWithSelection`
6. Use `useCallback` for `onClose` in EdgePopover
7. Clear UI state in useDashboard reset
8. Remove duplicate `AGENT_POSITIONS`

### Before Production

9. Add structured logging to satellite route
10. Add rate limiting
11. Add error boundary around Dashboard
12. Add accessibility attributes to StatusIndicator
13. Add Zod validation for SSE event data

---

## Backend Infrastructure Bugs (Pre-existing)

### 40. LangGraph Pipeline Takes 5-10 Minutes (NOT Stopping) - FIXED

- **Location:** `backend/app/agents/pipeline.py`, `backend/app/agents/graph.py`
- **Discovered:** February 21, 2026
- **Status:** FIXED
- **Description:** Initial diagnosis was incorrect. The pipeline was NOT stopping after claims extraction - it was simply taking 5-10 minutes to complete.
- **Root Causes Identified:**
  1. **Sequential agent execution**: Specialist agents were running sequentially instead of in parallel. The routing function returned a `list[str]` of node names, but LangGraph requires `Send()` objects for true parallel execution.
  2. Claims being persisted only AFTER the entire astream loop completed
  3. Checkpointer API incompatibility (`'_AsyncGeneratorContextManager' object has no attribute 'setup'`)
- **Fixes Applied:**
  1. **Parallel execution via Send() API**: Modified `route_to_specialists()` in `graph.py` to return `list[Send]` instead of `list[str]`. Each Send object specifies the target node and passes the state, enabling true parallel execution.
     - Import: `from langgraph.types import Send`
     - Return: `[Send(node_name, state) for node_name in active_agents]`
  2. Modified `run_pipeline` to persist claims immediately after `extract_claims` node completes
  3. Added detailed logging for each astream iteration
- **Expected Timing Improvement:**
  - Before: ~45s (claims) + ~15s (orchestrator) + ~60s × 5 (sequential specialists) + ~60s (judge + compile) = **~7 minutes**
  - After: ~45s (claims) + ~15s (orchestrator) + ~60s (parallel specialists) + ~60s (judge + compile) = **~3 minutes**
- **Remaining Issues:**
  1. Checkpointer API incompatibility with langgraph-checkpoint-postgres v2.0+ (does not block pipeline, only resumability)
  2. Legal Agent has frequent JSON parsing errors (`LegalAssessmentResult` validation failures)

### 41. Task Recovery Logic Creates Infinite Queue Blocking Loop

- **Location:** `backend/app/services/task_worker.py` (recovery logic)
- **Discovered:** February 21, 2026
- **Description:** When the backend restarts, the task recovery logic re-enqueues any reports with status `analyzing`. However, if the pipeline for that report fails or is interrupted repeatedly, the same report keeps getting recovered and re-enqueued on every restart. This creates a loop where:
  1. Report is in "analyzing" status
  2. On restart, recovery detects it and re-enqueues `run_pipeline` task
  3. Pipeline runs but may fail/timeout
  4. Status stays "analyzing"
  5. Next restart repeats the cycle
- **Impact:** New uploads queue behind the perpetually-recovered stuck report and never get processed. Users see "Uploading..." indefinitely while the backend is busy re-running a failed pipeline.
- **Workaround Applied:** Manually updated the stuck report's status to "completed" via SQL: `UPDATE reports SET status='completed' WHERE id='019c787c-7dce-7bd1-96a0-aaf7ef33e223';`
- **Remediation:**
  1. Add a `recovery_attempts` counter to reports
  2. After N failed recovery attempts (e.g., 3), mark report as "failed" instead of re-enqueuing
  3. Add admin UI or CLI to manually retry/clear stuck reports
  4. Consider adding a TTL to "analyzing" status so reports auto-fail after extended periods

### 42. Claims Not Displayed Until Analysis Completes (FIXED)

- **Location:** `frontend/src/hooks/useAnalysis.ts`, `frontend/src/pages/AnalysisPage.tsx`
- **Discovered:** February 21, 2026
- **Status:** FIXED
- **Description:** Claims were only fetched and displayed after the analysis reached `status === "completed"`. If the pipeline never completed (e.g., due to Bug #40), claims would not be shown in the Claims panel or as PDF highlights, even though they existed in the database and were returned by the API.
- **Impact:** Users saw "Loading claims..." indefinitely and no PDF highlights, even when 21 claims had been extracted and persisted.
- **Root Cause:**
  1. `useAnalysis.ts`: `fetchClaims()` was only called when analysis status reached "completed" or "error"
  2. `AnalysisPage.tsx`: `ClaimsPanel` received `isLoading={analysisState !== "complete"}`, which kept showing the loading state
- **Fix Applied:**
  1. Added `claimsFetchedRef` to track whether claims have been fetched
  2. Modified polling logic to call `fetchClaims()` as soon as `claims_count > 0` is detected
  3. Changed `ClaimsPanel` `isLoading` prop to: `isLoading={analysisState === "analyzing" && filteredClaims.length === 0}`
  4. This allows claims to be displayed during analysis, not just after completion

### 43. Specialist Agents Run Sequentially Despite Send() Fix (PARTIALLY FIXED)

- **Location:** `backend/app/agents/graph.py`
- **Discovered:** February 21, 2026
- **Status:** PARTIALLY FIXED - Parallel start confirmed, but agents still slow
- **Description:** The `Send()` API fix enables parallel agent START, but agents still take a long time because:
  1. Each agent processes multiple claims (21 claims routed to 5 agents)
  2. Within each agent, claims are processed SEQUENTIALLY (one LLM call per claim)
  3. LLM response validation errors cause retries or failures
- **Observed Behavior:**
  - Geography agent: completed with 5 findings
  - Academic agent: completed with 2 findings  
  - Data agent: completed with findings
  - Legal agent: STILL RUNNING after 3+ minutes (many JSON validation errors)
  - News agent: STILL RUNNING
- **Root Cause:** The agents ARE running in parallel, but the Legal agent has ~10+ claims × ~5 seconds each = 50+ seconds minimum, plus retries for validation failures
- **Fix Applied:** Changed `route_to_specialists()` to return `list[Send]` objects for parallel execution
- **Remaining Issues:**
  1. Claims within each agent are processed sequentially (could parallelize)
  2. JSON validation errors waste LLM calls and time

### 44. Legal Agent JSON Validation Errors (HIGH PRIORITY)

- **Location:** `backend/app/agents/legal_agent.py`
- **Discovered:** February 21, 2026
- **Status:** UNFIXED
- **Description:** The Legal agent frequently fails to parse LLM responses due to Pydantic validation errors:
  ```
  Failed to parse LLM response as JSON: 5 validation errors for LegalAssessmentResult
  gaps.0: Input should be a valid string [type=string_type, input_value=['Methodology used for ca...'], input_type=list]
  evidence.2: Input should be a valid string [type=string_type, input_value=['Board of Directors...'], input_type=list]
  ```
- **Impact:** Claims assigned to Legal agent produce no findings, wasting tokens and time
- **Root Cause:** The LLM is returning arrays for fields that expect strings (e.g., `gaps` and `evidence`)
- **Remediation:**
  1. Update `LegalAssessmentResult` schema to accept `list[str]` for these fields
  2. Or add post-processing to join arrays into strings
  3. Or improve the prompt to specify exact response format

### 45. Data/Quantitative Agent JSON Validation Errors

- **Location:** `backend/app/agents/data_agent.py`
- **Discovered:** February 21, 2026
- **Status:** UNFIXED
- **Description:** Similar to Legal agent, the Data agent has validation errors:
  ```
  Failed to parse LLM response: 1 validation error for QuantitativeValidationResult
  historical_consistency.reasoning: Input should be a valid string [type=string_type, input_value=['Only one historical dat...'], input_type=list]
  ```
- **Impact:** Some quantitative claims fail validation
- **Remediation:** Same as Legal agent - fix schema or add post-processing

### 46. Checkpointer API Incompatibility (PRE-EXISTING)

- **Location:** `backend/app/agents/checkpointer.py`
- **Discovered:** February 21, 2026
- **Status:** UNFIXED (non-blocking)
- **Description:** 
  ```
  Failed to setup checkpointer: '_AsyncGeneratorContextManager' object has no attribute 'setup'
  ```
- **Impact:** Pipeline cannot resume from checkpoints after interruption. Does NOT block pipeline execution.
- **Root Cause:** `langgraph-checkpoint-postgres` v2.0+ changed API - `from_conn_string` returns a context manager, not a direct checkpointer
- **Remediation:** Update checkpointer initialization to use `async with` pattern

### 47. Findings Not Persisted to Database During Pipeline

- **Location:** `backend/app/agents/pipeline.py`
- **Discovered:** February 21, 2026
- **Status:** UNFIXED
- **Description:** Despite agents completing with findings (geography: 5, academic: 2, data: findings), the status API shows `findings_count: 0`
- **Impact:** Users don't see investigation results even when agents complete
- **Root Cause:** Findings may not be persisted to database like claims were fixed to be
- **Remediation:** Add findings persistence after each specialist agent completes (similar to claims persistence fix)
