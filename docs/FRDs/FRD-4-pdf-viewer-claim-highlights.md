# Feature Requirements Document: FRD 4 -- PDF Viewer with Claim Highlights (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.1 (PDF highlighting), 4.2 (Claims Agent -- PDF highlighting), 7.2 (Analysis Page left panel) |
| **Type** | Feature |
| **Depends On** | FRD 2 (PDF Upload & Ingestion), FRD 3 (Claims Agent) |
| **Delivers** | Embedded PDF renderer (`react-pdf`), claim highlight overlays, highlight tooltips, page navigation, zoom controls, Analysis Page left panel, PDF serving endpoint |
| **Created** | 2026-02-09 |

---

## Summary

FRD 4 delivers the interactive PDF viewer with claim highlight overlays -- the Analysis Page's left panel as described in PRD Section 7.2. The viewer renders the original uploaded PDF using `react-pdf` (by wojtekmaj, MIT license -- replacing the originally planned `@pdf-viewer/react` which requires a commercial license), overlays colored highlights on claims extracted by the Claims Agent (FRD 3), and presents tooltips on click showing each claim's text, category, preliminary IFRS mapping, and agent reasoning. Highlights are positioned by a span-by-span text-matching algorithm that matches the claim's `claim_text` and `source_context` (provided by FRD 3) against the rendered PDF page text layer to compute bounding rectangles. Each highlight is color-coded by claim type (Geographic = forest green, Quantitative = coral/orange, Legal/Governance = deep purple, Strategic = amber/gold, Environmental = teal), matching the claim type color system established in FRD 3. The viewer supports page navigation (page input, previous/next buttons), zoom controls (fit-to-width, fit-to-page, percentage zoom), and scroll-to-page for navigating to a specific claim's location. FRD 4 also delivers a backend endpoint to serve the stored PDF binary as a downloadable/renderable resource, and restructures the Analysis Page from FRD 3's single-panel claims list into the three-panel layout described in PRD 7.2 (left: PDF viewer, center: placeholder for detective dashboard, right: placeholder for agent reasoning), with the claims list from FRD 3 remaining accessible within the right panel as a temporary measure until FRD 5 delivers the full agent reasoning stream.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `Report` SQLAlchemy model with `pdf_binary` (LargeBinary) column | FRD 0 | `app/models/report.py` |
| `Claim` SQLAlchemy model with `claim_text`, `claim_type`, `source_page`, `source_location` (JSONB), `ifrs_paragraphs` (JSONB), `priority`, `agent_reasoning` | FRD 0 | `app/models/claim.py` |
| `Claim` and `ClaimType` TypeScript types with `source_location.source_context` | FRD 3 | `src/types/claim.ts` |
| Frontend layout shell (`AppShell`, `Sidebar`, `Header`) | FRD 0 | `src/components/Layout/` |
| `AnalysisPage` with routing at `/analysis/:reportId` | FRD 0, FRD 3 | `src/pages/AnalysisPage.tsx` |
| `ClaimCard` component for displaying individual claims | FRD 3 | `src/components/Analysis/ClaimCard.tsx` |
| `useAnalysis` hook for analysis state management | FRD 3 | `src/hooks/useAnalysis.ts` |
| Claims list endpoint `GET /api/v1/analysis/{reportId}/claims` | FRD 3 | `app/api/routes/analysis.py` |
| Analysis status endpoint `GET /api/v1/analysis/{reportId}/status` | FRD 3 | `app/api/routes/analysis.py` |
| `react-pdf` (by wojtekmaj) installed as a frontend dependency | FRD 4 | `package.json` |
| PDFViewer component directory (`src/components/PDFViewer/`) | FRD 0 | Empty barrel `index.ts` |
| Claim type colors (CSS variables: `--claim-geographic`, `--claim-quantitative`, `--claim-legal`, `--claim-strategic`, `--claim-environmental`) | FRD 3 | `src/app.css` |
| PDF binary stored in the `reports` table for uploaded reports | FRD 2 | `Report.pdf_binary` |
| Extracted claims with `source_page` and `source_location.source_context` for each claim | FRD 3 | `claims` database table |
| API client methods: `getClaims()`, `getAnalysisStatus()` | FRD 3 | `src/services/api.ts` |

### Terms

| Term | Definition |
|---|---|
| PDF viewer | An embedded React component (using `react-pdf` / PDF.js) that renders a PDF document page-by-page with text selection, zoom, and navigation |
| Highlight overlay | A semi-transparent colored rectangle drawn on top of the rendered PDF page at the position where a claim's text appears |
| Text layer | The invisible text layer rendered by PDF.js on top of each PDF page, enabling text selection and search; used for text-matching to compute highlight positions |
| Bounding rectangle | A set of coordinates (`top`, `left`, `width`, `height`) relative to the PDF page that defines the position and size of a highlight overlay |
| Source context | The 1-2 sentences of surrounding text provided by the Claims Agent (FRD 3) that anchor a claim's position on the page; used for text matching |
| Claim type color | The color associated with each claim category (e.g., forest green for Geographic), consistent across the PDF viewer, claims list, and future detective dashboard |
| Three-panel layout | The Analysis Page layout from PRD 7.2: left (PDF viewer), center (detective dashboard), right (agent reasoning stream) |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: PDF Viewer with Claim Highlights

  Background:
    Given  FRD 0, FRD 1, FRD 2, and FRD 3 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    a sustainability report PDF has been uploaded, parsed, and analyzed
    And    claims have been extracted and stored with source page and context data

  Scenario: View the PDF in the Analysis Page
    Given  the user navigates to /analysis/{reportId}
    When   the Analysis Page loads
    Then   the page displays a three-panel layout
    And    the left panel renders the original PDF using the embedded viewer
    And    the PDF is loaded from the backend via GET /api/v1/reports/{reportId}/pdf
    And    the viewer displays the first page by default

  Scenario: Navigate PDF pages
    Given  the PDF viewer is displaying a multi-page document
    When   the user clicks the "Next Page" button
    Then   the viewer scrolls to the next page
    When   the user clicks the "Previous Page" button
    Then   the viewer scrolls to the previous page
    When   the user enters a page number in the page input field
    Then   the viewer scrolls to that page
    And    the current page indicator updates to reflect the visible page

  Scenario: Zoom the PDF
    Given  the PDF viewer is displaying a document
    When   the user clicks "Zoom In"
    Then   the zoom level increases by a fixed step
    When   the user clicks "Zoom Out"
    Then   the zoom level decreases by a fixed step
    When   the user selects "Fit to Width"
    Then   the PDF page scales to fit the panel width
    When   the user selects "Fit to Page"
    Then   the PDF page scales to fit the panel height

  Scenario: View claim highlights on the PDF
    Given  the PDF viewer is displaying a page with extracted claims
    When   the page renders
    Then   colored highlight overlays appear on the text of each claim on that page
    And    each highlight is colored by claim type (geographic=green, quantitative=orange, etc.)
    And    highlights are semi-transparent so the underlying text remains readable

  Scenario: Click a claim highlight to see details
    Given  the PDF viewer is displaying a page with highlighted claims
    When   the user clicks on a highlight overlay
    Then   a tooltip appears near the clicked highlight
    And    the tooltip shows: the claim text, claim type badge, priority badge, preliminary IFRS paragraph tags, and the Claims Agent's reasoning
    And    only one tooltip is visible at a time (clicking another highlight replaces it)
    When   the user clicks outside the tooltip or on a close button
    Then   the tooltip dismisses

  Scenario: Navigate to a claim's location from the claims list
    Given  the right panel displays the claims list
    When   the user clicks a "Go to page" link on a claim card
    Then   the PDF viewer scrolls to the page where that claim appears
    And    the corresponding highlight pulses briefly to draw attention

  Scenario: Handle claims with no position match
    Given  a claim's source_context could not be matched in the PDF text layer
    When   the page containing that claim renders
    Then   a fallback highlight bar is drawn (staggered vertically, visually distinct via --unmatched class)
    And    the claim remains visible in the claims list with its page number
    And    clicking "Go to page" still scrolls to the correct page

  Scenario: Handle PDF loading failure
    Given  the backend cannot serve the PDF binary
    When   the PDF viewer attempts to load the document
    Then   the left panel displays an error message: "Unable to load PDF. The document may not be available."
    And    a "Retry" button is shown that re-attempts the PDF fetch

  Scenario: Three-panel Analysis Page layout
    Given  the user navigates to /analysis/{reportId}
    When   the page loads with completed analysis
    Then   the left panel contains the PDF viewer with highlights
    And    the center panel contains a placeholder for the detective dashboard (FRD 12)
    And    the right panel contains the claims list from FRD 3 plus placeholder for agent reasoning (FRD 5)
    And    the panels are resizable via drag handles
```

---

## Table of Contents

1. [Backend PDF Serving Endpoint](#1-backend-pdf-serving-endpoint)
2. [PDF Viewer Component](#2-pdf-viewer-component)
3. [Claim Highlight Positioning](#3-claim-highlight-positioning)
4. [Highlight Overlay Rendering](#4-highlight-overlay-rendering)
5. [Highlight Tooltip](#5-highlight-tooltip)
6. [Page Navigation and Zoom Controls](#6-page-navigation-and-zoom-controls)
7. [Analysis Page Three-Panel Layout](#7-analysis-page-three-panel-layout)
8. [Cross-Panel Interactions](#8-cross-panel-interactions)
9. [Frontend Hooks and State](#9-frontend-hooks-and-state)
10. [Error Handling](#10-error-handling)
11. [Exit Criteria](#11-exit-criteria)
12. [Appendix A: Highlight Position Computation Algorithm](#appendix-a-highlight-position-computation-algorithm)
13. [Appendix B: Component Tree](#appendix-b-component-tree)
14. [Appendix C: Three-Panel Layout Wireframe](#appendix-c-three-panel-layout-wireframe)
15. [Design Decisions Log](#design-decisions-log)

---

## 1. Backend PDF Serving Endpoint

### 1.1 Overview

The PDF viewer requires access to the original PDF binary stored in the `reports` table (FRD 2). A dedicated backend endpoint serves the binary as a streamable response with the correct content type for `react-pdf` to consume.

### 1.2 Endpoint Definition

```
GET /api/v1/reports/{reportId}/pdf

Response 200:
  Content-Type: application/pdf
  Content-Disposition: inline; filename="{original_filename}"
  Body: raw PDF binary

Response 404:
{
  "detail": "Report not found."
}

Response 404 (no PDF binary):
{
  "detail": "PDF binary not available for this report."
}
```

### 1.3 Implementation Requirements

The system shall:

1. Accept a `reportId` path parameter (UUID string).
2. Load the `Report` record from the database by ID.
3. If the report does not exist, return `404`.
4. If the report's `pdf_binary` is `null`, return `404` with a descriptive message.
5. Return a `StreamingResponse` (or `Response`) with:
   - `media_type="application/pdf"`
   - `Content-Disposition: inline; filename="{report.filename}"` -- `inline` so the browser/viewer can render it rather than triggering a download.
   - The raw `pdf_binary` bytes as the response body.
6. Set appropriate cache headers: `Cache-Control: private, max-age=3600` -- the PDF is immutable once uploaded, so caching is safe and reduces redundant database reads during viewer interactions (page changes, zoom).

### 1.4 Route Registration

The endpoint shall be registered under a new reports router (`app/api/routes/reports.py`) with prefix `/reports` and tag `"Reports"`. This router is separate from the upload router (FRD 2) and the analysis router (FRD 3) because it serves report-level resources rather than upload or analysis operations.

```python
# app/api/routes/reports.py
from fastapi import APIRouter, Depends, Response
from fastapi.responses import Response as FastAPIResponse

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{report_id}/pdf")
async def get_report_pdf(report_id: str, db: AsyncSession = Depends(get_db)):
    ...
```

### 1.5 Router Registration

The reports router shall be registered in the root API router (`app/api/routes/__init__.py`) alongside the existing upload, analysis, stream, report, and chat routers.

---

## 2. PDF Viewer Component

### 2.1 Overview

The PDF viewer (`src/components/PDFViewer/PDFViewer.tsx`) is the primary component in the Analysis Page's left panel. It renders the uploaded PDF document, provides page navigation and zoom controls, and serves as the container for claim highlight overlays.

### 2.2 Library: `react-pdf` (by wojtekmaj)

The system uses `react-pdf` (MIT license, no watermarks or commercial license required) to render PDF documents. This library was chosen over the originally planned `@pdf-viewer/react` because the latter requires a commercial license for production use. `react-pdf` provides:

- Page-by-page PDF rendering with PDF.js under the hood
- Built-in text layer for text selection (`<Page renderTextLayer={true}>`)
- Annotation layer rendering (`<Page renderAnnotationLayer={true}>`)
- `Document` and `Page` components for declarative PDF rendering
- `onRenderTextLayerSuccess` callback for triggering highlight computation after text layer rendering

### 2.3 Component Interface

```typescript
interface PDFViewerProps {
  pdfUrl: string;                    // URL to fetch the PDF binary (GET /api/v1/reports/{reportId}/pdf)
  claims: Claim[];                   // Extracted claims for highlight rendering
  activeClaim: Claim | null;         // Currently selected claim (for scroll-to and tooltip display)
  onClaimClick: (claim: Claim) => void;  // Callback when a highlight is clicked
  onPageChange: (pageNumber: number) => void;  // Callback when the visible page changes
  currentPage: number;               // Current page number (1-indexed)
  goToPage?: (page: number) => void; // Optional external page navigation callback
}
```

### 2.4 PDF Loading

The system shall:

1. Construct the PDF URL from the report ID: `${API_BASE_URL}/reports/${reportId}/pdf`.
2. Pass the URL to the `react-pdf` `Document` component's `file` prop.
3. Configure the PDF.js worker source using a direct import of `pdfjs-dist/build/pdf.worker.mjs` via `pdfjs.GlobalWorkerOptions.workerSrc`.
4. Display a loading skeleton/spinner in the left panel while the PDF is being fetched and rendered.
5. Handle PDF load errors by displaying an error state within the panel (see Section 10).

### 2.5 Viewer Configuration

| Setting | Value | Rationale |
|---|---|---|
| Default zoom | Fit to width | Maximizes readability in the constrained left panel |
| Scroll mode | Vertical continuous | Natural scrolling through pages; matches user expectation for document viewing |
| Text layer | Enabled | Required for text selection and for computing highlight positions via text matching |
| Annotation layer | Enabled | Renders any PDF-native annotations; enabled for completeness with negligible overhead |
| Initial page | 1 | Start at the first page unless navigated to a specific claim |

---

## 3. Claim Highlight Positioning

### 3.1 Overview

The core challenge of FRD 4 is computing the visual position of each claim highlight on the rendered PDF page. The Claims Agent (FRD 3) provides textual anchoring data (`claim_text` and `source_context` stored in `source_location`) and a `source_page` number, but not pixel-level coordinates. FRD 4 must match the claim text against the PDF's text layer to determine where to draw each highlight.

### 3.2 Text Matching Strategy (Span-by-Span)

The system computes highlight positions using a **span-by-span** approach that avoids cross-span DOM `Range` objects (which cause index drift in PDF.js text layers):

1. **Wait for the text layer to be populated.** After each PDF page renders, `react-pdf`'s `onRenderTextLayerSuccess` fires. However, this callback fires *before* PDF.js finishes populating the text layer's `<span>` children in the DOM. The system uses a `MutationObserver` on the page wrapper element (which is a stable ref) to detect when leaf `<span>` elements with text content are actually present. A safety timeout of 10 seconds prevents indefinite waiting. The text layer element is re-queried fresh within the callback to avoid stale DOM references caused by React re-renders.

2. **Build a span index (`buildSpanIndex`).** Walk the leaf `<span>` children of the text layer (each corresponds to one PDF.js text item). Concatenate their `textContent` into a single `rawText` string, inserting an explicit space separator between consecutive spans (PDF.js spans don't include trailing inter-item whitespace). Each span's `[start, end)` character range in `rawText` is tracked in a `SpanEntry` array.

3. **Build a normalization map (`buildNormToRawMap`).** Normalize the raw text (collapse whitespace, unify quotes/dashes, lowercase) and build a character-level map from each index in the normalized string back to its corresponding index in the raw concatenated string. This allows translating a match in normalized space back to exact span positions.

4. **Search for the claim text.** For each claim assigned to the current page (`source_page`), try a cascade of candidates (most specific → least specific):
   - **Primary match:** The full `claim_text`, normalized and lowercased.
   - **Substring fallback:** The first 60 characters of `claim_text`, normalized. Skipped if the full text is 60 characters or fewer.
   - **Context-assisted fallback:** The `source_context` from `source_location`, normalized. Used when the claim text has been paraphrased or differs from the PDF's typographic rendering.
   - All candidates shorter than 10 characters are skipped to avoid false positives. The first successful match wins.

5. **Compute bounding rectangles span-by-span (`getRectsFromSpans`).** Once a match range `[matchStart, matchEnd)` in the raw string is found, identify all overlapping spans and compute rects for each:
   - **Full span overlap:** Use `span.getBoundingClientRect()` directly (simplest, most reliable — no DOM Range needed).
   - **Partial span overlap:** Create a `Range` *within that single span's text node only* (no cross-span ranges) and call `getClientRects()`.
   - All rects are converted to percentages of the text layer's bounding rect.

6. **Merge adjacent rects (`mergeAdjacentRects`).** Rects on the same line (top and height within 0.5% tolerance, gap < 1% of page width) are merged into a single wider rectangle to reduce visual clutter.

### 3.3 HighlightRect Type

```typescript
interface HighlightRect {
  top: number;       // Top position as percentage of page height
  left: number;      // Left position as percentage of page width
  width: number;     // Width as percentage of page width
  height: number;    // Height as percentage of page height
  pageNumber: number; // 1-indexed page number
}

interface ClaimHighlightData {
  claim: Claim;
  rects: HighlightRect[];  // One rect per line of highlighted text
  matched: boolean;        // Whether the text was successfully matched
}
```

### 3.4 Position Normalization

All highlight positions shall be stored as **percentages of the page dimensions** rather than absolute pixel values. This ensures highlights remain correctly positioned regardless of zoom level or container size. When rendering, the percentages are applied to the current page container dimensions.

### 3.5 Text Normalization

The system applies the following normalizations to **both** the page text and the claim text before comparison:

1. Replace smart single quotes (`\u2018`, `\u2019`) and prime (`\u2032`) with ASCII `'`.
2. Replace smart double quotes (`\u201C`, `\u201D`) and double prime (`\u2033`) with ASCII `"`.
3. Replace all Unicode dash variants (`\u2010`–`\u2015`, including en-dash and em-dash) with ASCII `-`.
4. Collapse multiple whitespace characters (spaces, tabs, newlines) into a single space.
5. Trim leading and trailing whitespace.
6. **Lowercase the entire string.** All matching is case-insensitive by default — there is no separate case-sensitive pass.

### 3.6 Performance Considerations

Highlight position computation is performed **per page, on text layer render**. All pages in the document are rendered in a continuous scroll container; each page's highlights are computed once when its text layer finishes populating. The system shall:

1. Maintain a cache of computed `ClaimHighlightData` keyed by page number, cleared when the claims list changes (detected by comparing sorted claim ID strings).
2. Compute highlights for a page when its text layer is first populated (triggered by the `onRenderTextLayerSuccess` callback + `MutationObserver` settling).
3. Skip recomputation for pages already in the cache (tracked via a `computedPagesRef` set).
4. Target completion within 50ms per page to avoid visible rendering jank.

### 3.7 Handling Multi-Page Claims

If a claim's text spans a page boundary (starts on one page and ends on the next), the system shall:

1. Highlight the matching portion on each page independently.
2. The Claims Agent assigns `source_page` to the page where the claim begins. If matching text is not found on `source_page`, attempt matching on `source_page + 1` as a fallback.

---

## 4. Highlight Overlay Rendering

### 4.1 Overview

Highlight overlays are semi-transparent colored rectangles drawn on top of the rendered PDF pages. Each overlay corresponds to a matched claim and is colored by claim type.

### 4.2 ClaimHighlight Component

```typescript
// src/components/PDFViewer/ClaimHighlight.tsx

interface ClaimHighlightProps {
  claimHighlight: ClaimHighlightData;
  isActive: boolean;           // Whether this claim is currently selected (tooltip visible)
  isPulsing?: boolean;         // Whether this highlight should show pulse animation (after cross-panel navigation)
  onClick: (claim: Claim) => void;
}
```

The `ClaimHighlight` component shall:

1. Render one `<div>` per `HighlightRect` in the claim's `rects` array.
2. Position each div absolutely within the page container using percentage-based `top`, `left`, `width`, and `height`.
3. Apply the claim type color as a semi-transparent background (`opacity: 0.25` for inactive, `opacity: 0.40` for active/hovered).
4. Apply a subtle left border (3px solid, full claim type color) to the first rect of each claim for visual anchoring.
5. Set `cursor: pointer` to indicate interactivity.
6. On click, call `onClick(claim)` to trigger the tooltip display.
7. On hover, increase opacity slightly to provide visual feedback.
8. When `isActive` is true (this claim's tooltip is shown), render with higher opacity and a subtle glow/outline effect using the claim type color.

### 4.3 Claim Type Colors

The highlight colors match the claim type color system from FRD 3:

| Claim Type | Color Name | Highlight Background | Border |
|---|---|---|---|
| `geographic` | Forest green | `rgba(34, 139, 34, 0.25)` | `rgb(34, 139, 34)` |
| `quantitative` | Coral/orange | `rgba(255, 127, 80, 0.25)` | `rgb(255, 127, 80)` |
| `legal_governance` | Deep purple | `rgba(128, 0, 128, 0.25)` | `rgb(128, 0, 128)` |
| `strategic` | Amber/gold | `rgba(255, 191, 0, 0.25)` | `rgb(255, 191, 0)` |
| `environmental` | Teal | `rgba(0, 128, 128, 0.25)` | `rgb(0, 128, 128)` |

These colors shall be defined as CSS custom properties (from FRD 3) and referenced in the component. The exact RGB values may be adjusted during implementation to ensure adequate contrast against typical PDF page backgrounds (white or off-white).

### 4.4 Highlight Layer Architecture

Highlights are rendered as an overlay layer on top of each PDF page. The system shall:

1. Inject a highlight container `<div>` as a sibling to each `react-pdf` `<Page>` component's canvas and text layer, within the page wrapper element.
2. The highlight container uses `position: absolute`, `top: 0`, `left: 0`, `width: 100%`, `height: 100%`, `pointer-events: none` (with `pointer-events: auto` on individual highlight divs) so that highlights do not interfere with text selection on the underlying text layer.
3. The highlight container has a `z-index` above the canvas but below any toolbar/UI elements.
4. Each highlight div within the container uses `pointer-events: auto` and `position: absolute` with percentage-based positioning.

### 4.5 Highlight Rendering Pipeline

For each rendered page:

1. `react-pdf`'s `onRenderTextLayerSuccess` fires for the page, triggering `computeHighlights(pageNum, pageWrapperEl)`.
2. `waitForTextLayer` uses a `MutationObserver` on the stable page wrapper element to detect when the text layer's leaf `<span>` elements are populated (since `onRenderTextLayerSuccess` fires before PDF.js finishes populating spans). The text layer element is re-queried fresh within the callback to avoid stale DOM references.
3. Filter the claims list to find claims where `source_page === currentPageNumber`.
4. If highlights for this page are not cached, run the span-by-span text matching algorithm (Section 3.2) to compute `ClaimHighlightData` for each claim on the page.
5. Cache the results (keyed by page number).
6. Render `ClaimHighlight` components for all claims (both matched and unmatched fallbacks).

---

## 5. Highlight Tooltip

### 5.1 Overview

When a user clicks a claim highlight, a tooltip appears showing the claim's details. This tooltip provides the same information that the Claims Agent produced in FRD 3, contextualized to the PDF location.

### 5.2 HighlightTooltip Component

```typescript
// src/components/PDFViewer/HighlightTooltip.tsx

interface HighlightTooltipProps {
  claim: Claim;
  anchorRect: HighlightRect;     // The rect to anchor the tooltip near
  onClose: () => void;
  onGoToClaim: (claim: Claim) => void;  // Navigate to claim in the claims list
  containerRef?: React.RefObject<HTMLDivElement | null>;  // Bounding container for positioning constraints
}
```

### 5.3 Tooltip Content

The tooltip shall display the following information in a compact card format:

1. **Header row:**
   - Claim type badge (colored pill with the type name, e.g., "Quantitative" in coral/orange).
   - Priority badge (`High` / `Medium` / `Low`).
   - Close button (X icon) at the top right.

2. **Claim text:**
   - The full claim text, displayed as a quoted block. If the text exceeds 200 characters, truncate with an ellipsis and a "Show more" toggle.

3. **IFRS mappings:**
   - A row of IFRS paragraph tag badges (e.g., "S2.29(a)(i)", "S1.46") rendered as small, rounded pills.
   - Each tag shows the `paragraph_id` from the claim's `ifrs_paragraphs` array.
   - If the claim has no IFRS mappings, show "No IFRS mapping" in muted text.

4. **Agent reasoning:**
   - A collapsible section labeled "Claims Agent Reasoning" that expands to show the full `agent_reasoning` text.
   - Collapsed by default to keep the tooltip compact.

5. **Footer:**
   - "Page {N}" indicator.
   - A "View in Claims List" link/button that scrolls the right panel to the corresponding claim card and highlights it.

### 5.4 Tooltip Positioning

The system shall position the tooltip using the following logic:

1. **Preferred position:** To the right of the highlight, vertically centered on the anchor rect. This avoids covering the highlighted text.
2. **Fallback (no room on right):** To the left of the highlight, vertically centered.
3. **Fallback (no room on either side):** Below the highlight, horizontally centered.
4. **Viewport constraint:** The tooltip must not extend beyond the visible bounds of the PDF viewer panel. If it would, adjust the position to stay within bounds.
5. **Fixed within the viewer:** The tooltip scrolls with the PDF content (it is positioned relative to the page, not the viewport), so it stays attached to its claim as the user scrolls.

### 5.5 Tooltip Dimensions

| Property | Value |
|---|---|
| Max width | 360px |
| Min width | 280px |
| Max height | 400px (scrollable if content exceeds) |
| Padding | 16px |
| Border radius | 8px |
| Background | Card background from the dark theme (`hsl(224, 20%, 14%)` or similar) |
| Border | 1px solid, claim type color at 50% opacity |
| Shadow | `0 4px 12px rgba(0, 0, 0, 0.5)` for visual lift |
| Z-index | Above highlights and text layer |

### 5.6 Tooltip Behavior

The system shall:

1. Show only one tooltip at a time. Clicking a different highlight replaces the current tooltip.
2. Dismiss the tooltip when:
   - The user clicks the close button.
   - The user clicks outside the tooltip and outside any highlight.
   - The user presses the `Escape` key.
3. Animate the tooltip entry with a subtle fade-in (150ms, ease-out).
4. Animate the tooltip exit with a fade-out (100ms, ease-in).

---

## 6. Page Navigation and Zoom Controls

### 6.1 Toolbar Component

```typescript
// src/components/PDFViewer/PDFToolbar.tsx

interface PDFToolbarProps {
  currentPage: number;
  totalPages: number;
  zoomLevel: number;          // Percentage (e.g., 100 = 100%)
  onPageChange: (page: number) => void;
  onZoomChange: (zoom: number) => void;
  onFitToWidth: () => void;
  onFitToPage: () => void;
}
```

### 6.2 Toolbar Layout

The toolbar is positioned at the top of the PDF viewer panel, above the rendered PDF content. It contains:

**Left group -- Page navigation:**
- Previous page button (`<` or chevron-left icon)
- Page input field: a narrow text input showing the current page number, editable by the user
- " / {totalPages}" label
- Next page button (`>` or chevron-right icon)

**Right group -- Zoom controls:**
- Zoom out button (`-` icon)
- Zoom level display (e.g., "100%") -- clickable to reset to fit-to-width
- Zoom in button (`+` icon)
- Fit-to-width button (icon: horizontal arrows)
- Fit-to-page button (icon: full-screen/expand arrows)

### 6.3 Page Navigation

The system shall:

1. Support scrolling to a specific page when the user enters a page number and presses Enter.
2. Clamp the page input to valid range: 1 to `totalPages`.
3. Update `currentPage` as the user scrolls through the document (derived from the topmost visible page in the viewport).
4. Support keyboard navigation: `ArrowUp` / `PageUp` for previous page, `ArrowDown` / `PageDown` for next page (when the viewer panel has focus).
5. Provide programmatic `scrollToPage(pageNumber)` for cross-panel interactions (see Section 8).

### 6.4 Zoom Controls

The system shall:

1. Support zoom levels from 50% to 300%, in 25% increments.
2. Default to "Fit to Width" on initial load.
3. "Fit to Width" calculates the zoom level that makes the PDF page width equal to the panel width (minus padding).
4. "Fit to Page" calculates the zoom level that fits the full page height within the visible panel area.
5. Zoom in/out buttons change the zoom by +/- 25%.
6. The zoom level is displayed as a percentage label.
7. Zoom is applied by adjusting the `width` prop on `react-pdf`'s `<Page>` component (`BASE_PAGE_WIDTH * zoomLevel / 100`). Zoom originates from the top-left of the scroll container.
8. Highlight positions automatically scale with zoom because they use percentage-based positioning (Section 3.4).

### 6.5 Toolbar Styling

| Property | Value |
|---|---|
| Height | 40px |
| Background | Panel background (slightly lighter than main background) |
| Border bottom | 1px solid border color from theme |
| Button size | 28px x 28px |
| Page input width | 48px |
| Font size | 13px for labels, 13px for input |

---

## 7. Analysis Page Three-Panel Layout

### 7.1 Overview

FRD 4 restructures the `AnalysisPage` from FRD 3's single-panel claims list into the three-panel layout described in PRD Section 7.2. The left panel contains the PDF viewer (this FRD), while the center and right panels are prepared with placeholders for future FRDs.

### 7.2 Panel Structure

| Panel | Position | Default Width | Content (FRD 4) | Future Content |
|---|---|---|---|---|
| Left | Left | 35% of viewport | PDF Viewer with claim highlights | -- (complete in FRD 4) |
| Center | Middle | 40% of viewport | Placeholder: "Detective Dashboard -- coming in FRD 12" | React Flow network graph (FRD 12) |
| Right | Right | 25% of viewport | Claims list (from FRD 3) + placeholder for agent reasoning tabs | SSE agent reasoning stream (FRD 5) |

### 7.3 Resizable Panels

The system shall implement resizable panels using a drag-handle approach:

1. Vertical dividers between panels that can be dragged horizontally to resize.
2. Minimum panel width: 250px (prevents panels from being collapsed to unusability).
3. Maximum panel width: 60% of the viewport (prevents one panel from dominating).
4. Cursor changes to `col-resize` when hovering over a divider.
5. During drag, panels resize smoothly without layout shifts in content.
6. Panel widths persist in the component state but do NOT persist across page navigations (session-only, not localStorage). This avoids complexity for MVP.

### 7.4 Implementation Approach

The system shall use CSS `display: flex` with adjustable `flex-basis` or CSS `grid` with adjustable column widths for the three-panel layout. A lightweight resize handler component manages the drag interactions.

```typescript
// src/components/Analysis/AnalysisLayout.tsx

interface AnalysisLayoutProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
}
```

### 7.5 Panel Identification

Each panel shall have a subtle header bar showing the panel name:

| Panel | Header Text |
|---|---|
| Left | "PDF Viewer" |
| Center | "Investigation Dashboard" |
| Right | "Claims & Reasoning" |

The header bar uses the muted foreground color and a small font size (12px), positioned at the very top of each panel. This provides orientation without consuming significant vertical space.

### 7.6 Analysis Page Updates

The `AnalysisPage` (`src/pages/AnalysisPage.tsx`) shall be updated to:

1. Wrap content in the `AnalysisLayout` component.
2. Place the `PDFViewer` component (this FRD) in the left panel.
3. Place a dashboard placeholder in the center panel.
4. Move the existing claims list (from FRD 3) into the right panel.
5. Retain all FRD 3 functionality (analysis trigger, polling, claim filtering, error handling).
6. Conditionally show the left panel only when the report has a PDF binary (it always should, but guard defensively).

### 7.7 Responsive Behavior

The three-panel layout targets desktop viewports (>= 1280px wide, per PRD 7.3). For narrower viewports:

1. **1024px - 1279px:** Hide the center panel; show only left (PDF) and right (claims) at 50%/50%.
2. **< 1024px:** Stack panels vertically (PDF on top, claims below). This is a graceful degradation -- the desktop experience is the primary target.

---

## 8. Cross-Panel Interactions

### 8.1 Claims List to PDF Navigation

When the user clicks a "Go to page" action on a claim card in the right panel (claims list), the system shall:

1. Call the PDF viewer's `scrollToPage(claim.source_page)` method.
2. Set the clicked claim as the `activeClaim` in the shared state.
3. After the page scrolls into view, briefly pulse the corresponding highlight (a CSS animation: scale 1.0 -> 1.02 -> 1.0 with increased opacity, over 600ms) to draw the user's attention.
4. Optionally open the tooltip for the active claim automatically.

### 8.2 PDF Highlight to Claims List

When the user clicks a highlight in the PDF viewer and opens the tooltip, the "View in Claims List" action in the tooltip shall:

1. Scroll the right panel to the corresponding `ClaimCard` component.
2. Briefly highlight the claim card in the right panel (a subtle background flash using the claim type color at 10% opacity, fading over 1 second).
3. Expand the claim card's reasoning section if it was collapsed.

### 8.3 Shared Active Claim State

The `AnalysisPage` shall maintain a shared `activeClaim` state that coordinates between panels:

```typescript
const [activeClaim, setActiveClaim] = useState<Claim | null>(null);
```

- Setting `activeClaim` from the right panel (click on a claim card's page link) scrolls the PDF and pulses the highlight.
- Setting `activeClaim` from the left panel (click on a highlight) opens the tooltip and scrolls the claims list.
- Setting `activeClaim` to `null` (click outside, Escape key) dismisses the tooltip and clears the highlight.

### 8.4 Claim Card Enhancement

The existing `ClaimCard` component (FRD 3) shall be enhanced with:

1. A "Page {N}" link that triggers the cross-panel navigation to the PDF viewer (see Section 8.1).
2. A `ref` (using `React.forwardRef` or a callback ref) so that the right panel can programmatically scroll to a specific claim card.
3. An `isActive` prop that applies a subtle visual indicator (e.g., left border glow) when the claim is the active claim.

---

## 9. Frontend Hooks and State

### 9.1 PDF Viewer State (Inline)

PDF viewer state (loading, error, zoom, page navigation, page refs) is managed directly within the `PDFViewer` component via `useState` and `useRef` hooks rather than extracted into a separate `usePDFViewer` hook. This keeps the state co-located with the rendering logic and avoids prop drilling. Key state:

- `totalPages` — set by `onLoadSuccess` callback from `react-pdf` `Document`
- `zoomLevel` — percentage (50–300), default 100, step 25
- `error` / `isLoading` — loading lifecycle
- `pageRefs` — `Map<number, HTMLDivElement>` for stable page wrapper references
- `isProgrammaticScrollRef` — gates `IntersectionObserver` updates during `goToPage`
- Current page tracking uses an `IntersectionObserver` on the scroll container (see Section 9.4)

### 9.2 useClaimHighlights Hook

The system implements a hook for managing highlight computation and caching:

```typescript
// src/hooks/useClaimHighlights.ts

interface UseClaimHighlightsReturn {
  // Highlight data
  getHighlightsForPage: (pageNumber: number) => ClaimHighlightData[];

  // Computation — accepts the page WRAPPER element (not the text layer directly).
  // The hook internally waits for the text layer to populate and re-queries it
  // fresh to avoid stale DOM references from React re-renders.
  computeHighlights: (pageNumber: number, pageWrapperEl: HTMLElement) => void;

  // State
  isComputing: boolean;
  matchRate: number;    // Percentage of claims successfully matched (0-100)
}

function useClaimHighlights(claims: Claim[]): UseClaimHighlightsReturn;
```

Key internal functions:
- `waitForTextLayer(pageWrapperEl, callback)` — MutationObserver-based wait for text layer span population (max 10s timeout)
- `findReadyTextLayer(pageWrapperEl)` — checks if text layer has leaf spans with content
- `buildSpanIndex(textLayerEl)` — builds `SpanEntry[]` + `rawText` with explicit space separators
- `buildNormToRawMap(rawText)` — character-level normalized→raw index map
- `getRectsFromSpans(spans, matchStart, matchEnd, pageRect, pageNumber)` — span-by-span rect computation
- `mergeAdjacentRects(rects)` — merges same-line rects within 0.5% tolerance

### 9.3 State Flow

```
AnalysisPage
├── activeClaim: Claim | null          (shared between panels)
├── useAnalysis(reportId)              (from FRD 3: analysis state, claims, filters)
│
├── Left Panel: PDFViewer
│   ├── useClaimHighlights(claims)     (highlight computation — called inside PDFViewer)
│   ├── PDFToolbar (navigation, zoom)
│   ├── PDF rendering (react-pdf Document + Page)
│   │   └── [Per-page wrapper div]
│   │       ├── <Page> (react-pdf)
│   │       └── .pdf-viewer__page-highlights (overlay)
│   │           └── ClaimHighlight[] (one per claim, matched or fallback)
│   ├── HighlightTooltip (conditional, one at a time)
│   └── IntersectionObserver (current page tracking)
│
├── Center Panel: Placeholder
│   └── "Detective Dashboard -- coming in FRD 12"
│
└── Right Panel: Claims & Reasoning
    ├── Filter controls (type, priority -- from FRD 3)
    └── ClaimCard[] (scrollable list -- from FRD 3, enhanced)
```

### 9.4 Page Tracking (IntersectionObserver)

The current page number is tracked via an `IntersectionObserver` attached to the scroll container, observing all page wrapper elements at thresholds `[0, 0.25, 0.5, 0.75, 1]`. The page with the highest `intersectionRatio` is reported as the current page. During programmatic scrolls (triggered by `goToPage`), the observer's callback is gated by an `isProgrammaticScrollRef` flag to prevent feedback loops between the observer and the scroll command.

---

## 10. Error Handling

### 10.1 PDF Loading Errors

| Error | Trigger | User Message | Recovery |
|---|---|---|---|
| PDF endpoint returns 404 | Report not found or PDF binary not stored | "Unable to load PDF. The document may not be available." | "Retry" button re-fetches the PDF URL |
| Network error fetching PDF | Backend unreachable, timeout | "Unable to connect to the server. Please check your connection." | "Retry" button re-fetches |
| PDF.js rendering error | Corrupt PDF binary, unsupported PDF features | "The PDF could not be rendered. The file may be corrupt." | Display the claims list in the right panel (analysis is still usable without the PDF) |
| PDF worker initialization failure | Worker script failed to load | "PDF viewer failed to initialize. Please refresh the page." | "Refresh" button reloads the page |

### 10.2 Highlight Computation Errors

| Error | Trigger | Handling |
|---|---|---|
| Text layer not available | `react-pdf` renders without a text layer, or the `MutationObserver` times out (10s) | Skip highlight rendering for the affected page; claims remain accessible in the claims list |
| Text match fails for a claim | Claim text not found in the PDF text layer (OCR artifacts, markdown normalization differences) | Mark the claim as `matched: false`; render a **fallback highlight** — a staggered horizontal bar (90% width, positioned vertically by claim index) with an `--unmatched` CSS modifier class to visually distinguish it from matched highlights. The claim also remains in the claims list with "Page {N}" as a navigation aid |
| Performance timeout | Highlight computation exceeds 200ms for a page | Abort computation for remaining unmatched claims on that page; render highlights for successfully matched claims; log a warning |

### 10.3 Graceful Degradation

The PDF viewer and highlights are a visual enhancement layer on top of the claims list. If the PDF cannot be loaded or highlights cannot be computed, the system degrades gracefully:

1. The claims list in the right panel remains fully functional with all claim data.
2. The left panel shows an appropriate error state rather than crashing the entire Analysis Page.
3. Cross-panel navigation ("Go to page") is disabled when the PDF is unavailable but the claim card data is still shown.

---

## 11. Exit Criteria

FRD 4 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | PDF binary is served by the backend | `curl http://localhost:8000/api/v1/reports/{reportId}/pdf` returns a valid PDF binary with `Content-Type: application/pdf` |
| 2 | PDF renders in the left panel | Navigate to `/analysis/{reportId}` and verify the PDF is visible in the left panel |
| 3 | Three-panel layout is displayed | Verify the Analysis Page shows three panels: PDF viewer (left), placeholder (center), claims list (right) |
| 4 | Panels are resizable | Drag the divider between panels and verify both panels resize smoothly |
| 5 | Page navigation works | Click next/previous page buttons; enter a page number; verify the viewer navigates to the correct page |
| 6 | Zoom controls work | Click zoom in/out; use fit-to-width and fit-to-page; verify the PDF scales correctly |
| 7 | Claim highlights are visible on the PDF | View a page with extracted claims; verify colored highlights appear on the claim text |
| 8 | Highlights are colored by claim type | Verify geographic claims are green, quantitative are orange, etc. |
| 9 | Clicking a highlight shows a tooltip | Click a highlight; verify the tooltip appears with claim text, type, priority, IFRS tags, and reasoning |
| 10 | Only one tooltip is visible at a time | Click one highlight, then another; verify the first tooltip is replaced |
| 11 | Tooltip dismisses correctly | Click outside the tooltip; press Escape; click the close button; verify the tooltip dismisses in all cases |
| 12 | "Go to page" on claim card scrolls PDF | In the right panel, click "Page N" on a claim card; verify the PDF scrolls to that page |
| 13 | Highlight pulses after navigation | After scrolling to a page via a claim card, verify the corresponding highlight briefly pulses |
| 14 | "View in Claims List" from tooltip works | Click a highlight, then click "View in Claims List" in the tooltip; verify the right panel scrolls to the claim card |
| 15 | Highlights survive zoom changes | Zoom in and out; verify highlights remain correctly positioned over the claim text |
| 16 | Unmatched claims degrade gracefully | For claims where text matching fails, verify a visually distinct fallback highlight bar is shown (not the precise text position) and the claim remains accessible in the claims list |
| 17 | PDF loading error is handled | Simulate a 404 for the PDF endpoint; verify the left panel shows an error message with a retry option |
| 18 | Current page indicator updates on scroll | Scroll through the PDF; verify the page number in the toolbar updates to reflect the visible page |
| 19 | Claims list functionality is preserved | Verify all FRD 3 claims list features still work: filtering by type, filtering by priority, collapsible reasoning |
| 20 | Performance is acceptable | Navigate through a 200-page PDF; verify highlights render within 200ms per page without visible jank |

---

## Appendix A: Highlight Position Computation Algorithm

### A.1 Pseudocode

```
function computeHighlights(pageNumber, pageWrapperEl, claims):
    // Step 0: Wait for text layer to be populated
    // react-pdf fires onRenderTextLayerSuccess BEFORE PDF.js populates <span> children.
    // We use a MutationObserver on the stable pageWrapperEl to detect when leaf spans appear.
    waitForTextLayer(pageWrapperEl, function(textLayerEl):

        pageRect = textLayerEl.getBoundingClientRect()

        // Step 1: Build span index with explicit space separators
        { spans, rawText } = buildSpanIndex(textLayerEl)
        //   - Walk leaf <span> children of the text layer
        //   - For each span: rawText += " " (if not first) + span.textContent
        //   - Track each span's [start, end) range in rawText

        // Step 2: Normalize and build character-level reverse map
        normText = normalize(rawText)       // lowercase, collapse whitespace, unify quotes/dashes
        normToRaw = buildNormToRawMap(rawText)  // normIndex → rawIndex

        // Step 3: Match each claim using a candidate cascade
        pageClaims = claims.filter(c => c.source_page === pageNumber)
        results = []

        for each claim in pageClaims:
            candidates = [
                claim.claim_text,                              // full text
                claim.claim_text.slice(0, 60) if len > 60,    // substring fallback
                claim.source_location?.source_context           // context fallback
            ].filter(Boolean)

            matched = false
            for candidate in candidates:
                normNeedle = normalize(candidate)
                if normNeedle.length < 10: continue

                normIdx = normText.indexOf(normNeedle)
                if normIdx === -1: continue

                // Map normalized range → raw range via normToRaw
                rawStart = normToRaw[normIdx].rawIndex
                rawEnd   = normToRaw[normIdx + normNeedle.length - 1].rawIndex + 1

                // Step 4: Get rects span-by-span (NO cross-span Ranges)
                rawRects = getRectsFromSpans(spans, rawStart, rawEnd, pageRect)
                //   - Full span overlap → span.getBoundingClientRect()
                //   - Partial span → Range within that single span's text node
                //   - Convert all rects to % of pageRect

                if rawRects.length > 0:
                    rects = mergeAdjacentRects(rawRects)   // same-line merge (0.5% tolerance)
                    results.push({ claim, rects, matched: true })
                    matched = true
                    break

            if not matched:
                // Fallback: stagger unmatched claims vertically
                results.push({ claim, rects: [{ top: 8 + i*6, left: 5, width: 90, height: 2.5 }], matched: false })

        cache[pageNumber] = results
    )

function waitForTextLayer(pageWrapperEl, callback):
    // Fast path: if text layer already has leaf spans, fire via rAF
    ready = findReadyTextLayer(pageWrapperEl)
    if ready:
        requestAnimationFrame(() =>
            fresh = findReadyTextLayer(pageWrapperEl)  // re-query to survive React re-renders
            if fresh: callback(fresh)
        )
        return

    // Slow path: MutationObserver on pageWrapperEl (stable ref)
    observer = new MutationObserver(() =>
        if findReadyTextLayer(pageWrapperEl): settle()
    )
    observer.observe(pageWrapperEl, { childList: true, subtree: true })
    timer = setTimeout(settle, 10_000)   // safety timeout
```

### A.2 Text Normalization Function

```typescript
function normalize(text: string): string {
  return text
    .replace(/[\u2018\u2019\u2032]/g, "'")                    // Smart single quotes + prime
    .replace(/[\u201C\u201D\u2033]/g, '"')                    // Smart double quotes + double prime
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2015]/g, '-') // All Unicode dashes
    .replace(/\s+/g, ' ')                                     // Collapse whitespace
    .trim()
    .toLowerCase();                                            // Case-insensitive matching
}
```

---

## Appendix B: Component Tree

```
AnalysisPage
├── AnalysisLayout
│   ├── ResizeHandle (between left and center)
│   ├── ResizeHandle (between center and right)
│   │
│   ├── [Left Panel]
│   │   └── PDFViewer
│   │       ├── useClaimHighlights(claims)
│   │       ├── PDFToolbar
│   │       │   ├── PageNavigation (prev, input, next)
│   │       │   └── ZoomControls (-, level, +, fit-width, fit-page)
│   │       ├── Document (react-pdf)
│   │       │   └── [Per page]
│   │       │       └── .pdf-viewer__page-wrapper (div, holds ref)
│   │       │           ├── Page (react-pdf, onRenderTextLayerSuccess)
│   │       │           └── .pdf-viewer__page-highlights (overlay)
│   │       │               └── ClaimHighlight[] (one per claim, matched or fallback)
│   │       └── HighlightTooltip (conditional, one at a time, positioned via containerRef)
│   │
│   ├── [Center Panel]
│   │   └── DashboardPlaceholder
│   │       └── "Investigation Dashboard -- coming in FRD 12"
│   │
│   └── [Right Panel]
│       └── ClaimsPanel
│           ├── PanelHeader ("Claims & Reasoning")
│           ├── FilterBar (type filter, priority filter)
│           └── ClaimCard[] (scrollable, from FRD 3, enhanced with page links)
```

---

## Appendix C: Three-Panel Layout Wireframe

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Header                                                                       │
├─────────────────────┬────────────────────────────┬──────────────────────────┤
│ PDF Viewer          │ Investigation Dashboard     │ Claims & Reasoning       │
│                     │                              │                          │
│ ┌─────────────────┐ │                              │ ┌──────────────────────┐ │
│ │◄ Page 45/142  ► │ │                              │ │ Filter: All Types ▼  │ │
│ │  -  100%  + ⇔ ⊞ │ │                              │ │ Priority: All ▼      │ │
│ ├─────────────────┤ │                              │ ├──────────────────────┤ │
│ │                 │ │                              │ │ ┌────────────────────┐│ │
│ │  PDF content    │ │    Detective Dashboard       │ │ │ ■ Scope 1 emis...  ││ │
│ │  with ████████  │ │                              │ │ │ Quantitative | High││ │
│ │  highlighted    │ │    coming in FRD 12          │ │ │ Page 45 ↗          ││ │
│ │  claims         │ │                              │ │ │ S2.29(a)(i) S1.46  ││ │
│ │                 │ │                              │ │ └────────────────────┘│ │
│ │  ┌───────────┐  │ │                              │ │ ┌────────────────────┐│ │
│ │  │ Tooltip   │  │ │                              │ │ │ ■ Reforestation... ││ │
│ │  │ Quant.  H │  │ │                              │ │ │ Geographic | Med   ││ │
│ │  │ "Scope 1" │  │ │                              │ │ │ Page 72 ↗          ││ │
│ │  │ S2.29(a)  │  │ │                              │ │ │ S2.14(a)(ii)       ││ │
│ │  │ ▸ Reason  │  │ │                              │ │ └────────────────────┘│ │
│ │  └───────────┘  │ │                              │ │                        │ │
│ │                 │ │                              │ │ ... more claims ...    │ │
│ └─────────────────┘ │                              │ └──────────────────────┘ │
├─────────────────────┴────────────────────────────┴──────────────────────────┤
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Text-matching for highlight positioning over storing PDF coordinates in the Claims Agent | The Claims Agent (FRD 3) operates on extracted markdown text, not on the PDF layout. Storing bounding box coordinates would require the Claims Agent to have access to the PDF renderer, coupling agent logic to presentation. Text matching decouples these concerns: the agent extracts semantics, and the viewer computes positions. The `source_context` from FRD 3 provides sufficient anchoring for reliable matching. |
| Percentage-based highlight positions over absolute pixel positions | Percentage-based positioning automatically adapts to zoom level and container resizing without recalculation. Absolute pixel positions would require recomputing on every zoom or resize event. |
| Per-page highlight computation (on render) over upfront computation for all pages | A 200-page PDF may have claims scattered across many pages. Computing highlights upfront for all 200 pages would delay the initial render. Per-page computation (with caching) spreads the cost and only computes for pages the user actually views. |
| Single tooltip instance over per-highlight tooltips | Rendering 100+ tooltip components (one per claim) even if hidden would bloat the DOM. A single tooltip instance repositioned to the active claim is lighter and enforces the "one tooltip at a time" UX requirement. |
| Separate `/reports/{reportId}/pdf` endpoint over embedding PDF in the status response | The PDF binary can be 10-50MB. Including it in a JSON API response would require base64 encoding (33% size overhead) and break the JSON streaming model. A dedicated binary endpoint with proper `Content-Type` allows the browser/viewer to handle the PDF natively with streaming, caching, and range requests. |
| `Cache-Control: private, max-age=3600` for PDF endpoint | The PDF binary is immutable after upload -- it never changes. Caching avoids redundant 10-50MB fetches when the user navigates away and back, or when the page re-renders. `private` prevents shared caches from storing potentially sensitive sustainability reports. |
| Fit-to-width as default zoom over 100% | The left panel is typically 35% of the viewport width, which is narrower than most PDF page widths at 100% zoom. Fit-to-width ensures the full page width is visible without horizontal scrolling, providing a better reading experience in the constrained panel. |
| Inline PDF viewer state over a separate `usePDFViewer` hook | PDF viewer state (zoom, loading, error, page refs) is tightly coupled to the `PDFViewer` component's rendering logic. Extracting it into a separate hook would create unnecessary prop drilling without reuse benefit. |
| IntersectionObserver for page tracking over library-provided page tracking | `react-pdf` does not provide built-in current-page tracking. An `IntersectionObserver` on the scroll container observing page wrapper elements (thresholds 0–1) accurately detects the most-visible page during user scroll. A `isProgrammaticScrollRef` flag gates the observer during `goToPage` calls to prevent feedback loops. |
| CSS flexbox for three-panel layout over a library (e.g., react-resizable-panels) | A third-party resize panel library adds a dependency for straightforward functionality. CSS flexbox with simple mouse event handlers for resize provides the same UX with zero additional dependencies and full styling control. |
| Center panel placeholder in FRD 4 over waiting for FRD 12 | Establishing the three-panel layout now creates the spatial structure for the detective dashboard (FRD 12) and agent reasoning panel (FRD 5). Building these FRDs on top of an existing three-panel layout is simpler than restructuring a single-panel or two-panel page later. |
| Highlight overlays as positioned `<div>` elements over SVG or canvas drawing | DOM-based highlights (absolutely positioned divs) integrate naturally with React's rendering model, support CSS transitions/animations for hover and active states, and respond to click events without custom hit-testing. SVG or canvas overlays would require manual coordinate management and event delegation. |
| Claims list moved to right panel over remaining in a separate tab/page | PRD 7.2 specifies the claims list as part of the right panel's "Agent Reasoning" section. Co-locating the claims list with the PDF viewer enables cross-panel interactions (click claim -> scroll PDF) that would be impossible on a separate page. The claims list is interim content for the right panel until FRD 5 delivers agent reasoning tabs. |
| `react-pdf` (wojtekmaj) over `@pdf-viewer/react` | `@pdf-viewer/react` requires a commercial license for production use. `react-pdf` is MIT-licensed, provides the same PDF.js foundation, and offers `Document`/`Page` components with `onRenderTextLayerSuccess` callbacks sufficient for highlight injection. |
| MutationObserver-based `waitForTextLayer` over `requestAnimationFrame` | `react-pdf`'s `onRenderTextLayerSuccess` callback fires before PDF.js finishes populating `<span>` children in the DOM. A simple `requestAnimationFrame` is insufficient; a `MutationObserver` on the stable page wrapper element reliably detects when text spans are present. The text layer element is re-queried fresh within the callback to avoid stale DOM references from React re-renders. |
| Span-by-span rect computation over cross-span DOM Range API | Creating a single Range that spans across multiple `<span>` elements in the PDF.js text layer causes index drift — the Range endpoints land in the wrong span, cutting highlights short. Computing rects per-span (full-span → `getBoundingClientRect()`; partial-span → Range within a single text node) eliminates this drift entirely. |
| `react-pdf` `onRenderTextLayerSuccess` callback for highlight injection | Using the library's intended extension points ensures compatibility with future library updates and avoids fragile DOM manipulation hacks. |
| Three-tier text matching fallback (exact → first-60-chars substring → source_context) over single-method matching | PDF text extraction by PDF.js may differ subtly from PyMuPDF4LLM markdown extraction (different whitespace handling, ligature interpretation, table formatting). A cascading fallback strategy maximizes match rate. The 60-character substring catches cases where the tail of the claim text diverges. The `source_context` fallback leverages the broader text context when the exact claim text has been paraphrased by the Claims Agent. Candidates shorter than 10 characters are skipped to avoid false positives. |
| No thumbnail sidebar for MVP over a full thumbnail navigation panel | A page thumbnail sidebar consumes horizontal space in an already space-constrained left panel. The page input field and previous/next buttons provide sufficient navigation for hackathon scope. Thumbnail navigation is a post-MVP enhancement. |
