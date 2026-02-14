/**
 * useClaimHighlights - Hook for computing claim highlight positions.
 * Implements FRD 4 Section 5.1 (Highlight Position Computation).
 *
 * Strategy: **span-by-span** matching.
 *
 *   1. Walk the direct <span> children of the text layer (each corresponds
 *      to one PDF.js text item).
 *   2. Build a concatenated string from each span's textContent, tracking
 *      which character range belongs to which span element.
 *   3. Normalize both the concatenated page text and the claim text, then
 *      search for the claim.
 *   4. Map the normalized match range back to span-relative character
 *      offsets using a normIndex → spanIndex + charOffset map.
 *   5. For each overlapping span, get its getBoundingClientRect() directly
 *      (or create a sub-Range *within that single span's text node* if the
 *      match starts/ends mid-span).
 *
 * This avoids all cross-span Range issues and the index drift that caused
 * highlights to be cut off.
 */

import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import type { Claim } from "@/types/claim";
import type {
  ClaimHighlightData,
  HighlightRect,
  HighlightCache,
} from "@/components/PDFViewer/types";

export interface UseClaimHighlightsReturn {
  getHighlightsForPage: (pageNumber: number) => ClaimHighlightData[];
  computeHighlights: (pageNumber: number, pageWrapperEl: HTMLElement) => void;
  isComputing: boolean;
  matchRate: number;
}

/** CSS selector for the react-pdf text layer within a page wrapper. */
const TEXT_LAYER_SELECTOR = ".react-pdf__Page__textContent";

// ─── Types ─────────────────────────────────────────────────────────────────

/** One span in the text layer with its character range in the concatenated text. */
interface SpanEntry {
  element: HTMLElement;
  text: string;
  /** Start index (inclusive) in the concatenated raw string */
  start: number;
  /** End index (exclusive) in the concatenated raw string */
  end: number;
}

/**
 * Maps a normalized-string index to a position in the span-indexed raw
 * string. We need this because normalization (whitespace collapse,
 * lowercasing, quote replacement) changes character positions.
 */
interface NormMapEntry {
  /** Index into the raw concatenated string */
  rawIndex: number;
}

// ─── Constants ─────────────────────────────────────────────────────────────

/** Maximum time (ms) to wait for text layer spans before giving up. */
const MAX_SPAN_WAIT_MS = 10_000;

// ─── Helpers ───────────────────────────────────────────────────────────────

/** Normalize text for fuzzy matching (collapse whitespace, unify quotes, lowercase). */
function normalize(text: string): string {
  return text
    .replace(/[\u2018\u2019\u2032]/g, "'")
    .replace(/[\u201C\u201D\u2033]/g, '"')
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2015]/g, "-")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

/**
 * Build a character-level map: normIndex → rawIndex.
 *
 * After normalizing a raw string (collapsing whitespace, lowercasing, etc.)
 * each character in the normalized string came from a specific position in
 * the raw string. This map tracks that so we can translate a match in
 * normalized space back to the raw concatenated string.
 */
function buildNormToRawMap(raw: string): NormMapEntry[] {
  const map: NormMapEntry[] = [];
  let inSpace = false;
  let started = false;

  for (let i = 0; i < raw.length; i++) {
    const isWS = /\s/.test(raw[i]);

    if (isWS) {
      if (started && !inSpace) {
        map.push({ rawIndex: i }); // single space representative
        inSpace = true;
      }
    } else {
      started = true;
      inSpace = false;
      map.push({ rawIndex: i });
    }
  }

  return map;
}

/**
 * Walk the <span> children of the text layer and build a SpanEntry index.
 *
 * PDF.js renders each text item as a <span> with absolute positioning.
 * We add a single space between spans to mirror how humans read the text
 * (PDF.js spans don't include trailing inter-item whitespace).
 */
function buildSpanIndex(textLayerEl: HTMLElement): {
  spans: SpanEntry[];
  rawText: string;
} {
  const spans: SpanEntry[] = [];
  let rawText = "";

  // PDF.js text layer: direct children are <span> elements, each is one
  // text item. Some may be nested (e.g. <span><br><span>), so we grab
  // only leaf-level spans containing text.
  const children = textLayerEl.querySelectorAll("span");

  for (const el of children) {
    // Skip spans that contain other spans (non-leaf)
    if (el.querySelector("span")) continue;

    const text = el.textContent ?? "";
    if (text.length === 0) continue;

    // Separator space between spans
    if (rawText.length > 0) {
      rawText += " ";
    }

    const start = rawText.length;
    rawText += text;
    const end = rawText.length;

    spans.push({ element: el, text, start, end });
  }

  return { spans, rawText };
}

/**
 * Given a match in the raw concatenated text [matchStart, matchEnd),
 * find all overlapping spans and compute a bounding rect for the matched
 * portion within each span.
 *
 * For full-span matches: use span.getBoundingClientRect() directly.
 * For partial spans: create a Range within that single span's text node.
 * No cross-span Ranges are ever created.
 */
function getRectsFromSpans(
  spans: SpanEntry[],
  matchStart: number,
  matchEnd: number,
  pageRect: DOMRect,
  pageNumber: number,
): HighlightRect[] {
  const rects: HighlightRect[] = [];

  for (const span of spans) {
    // Skip spans that don't overlap the match range
    if (span.end <= matchStart || span.start >= matchEnd) continue;

    // Character range within this span's text
    const localStart = Math.max(0, matchStart - span.start);
    const localEnd = Math.min(span.text.length, matchEnd - span.start);

    if (localStart >= localEnd) continue;

    // Full span → use getBoundingClientRect (simplest, most reliable)
    if (localStart === 0 && localEnd === span.text.length) {
      const rect = span.element.getBoundingClientRect();
      if (rect.width > 1 && rect.height > 1) {
        rects.push({
          top: ((rect.top - pageRect.top) / pageRect.height) * 100,
          left: ((rect.left - pageRect.left) / pageRect.width) * 100,
          width: (rect.width / pageRect.width) * 100,
          height: (rect.height / pageRect.height) * 100,
          pageNumber,
        });
      }
      continue;
    }

    // Partial span → Range within this single text node
    const textNode = span.element.firstChild;
    if (!textNode || textNode.nodeType !== Node.TEXT_NODE) {
      // Fallback: use the full span rect
      const rect = span.element.getBoundingClientRect();
      if (rect.width > 1 && rect.height > 1) {
        rects.push({
          top: ((rect.top - pageRect.top) / pageRect.height) * 100,
          left: ((rect.left - pageRect.left) / pageRect.width) * 100,
          width: (rect.width / pageRect.width) * 100,
          height: (rect.height / pageRect.height) * 100,
          pageNumber,
        });
      }
      continue;
    }

    try {
      const range = document.createRange();
      range.setStart(textNode, localStart);
      range.setEnd(textNode, localEnd);
      const domRects = range.getClientRects();
      for (const r of domRects) {
        if (r.width > 1 && r.height > 1) {
          rects.push({
            top: ((r.top - pageRect.top) / pageRect.height) * 100,
            left: ((r.left - pageRect.left) / pageRect.width) * 100,
            width: (r.width / pageRect.width) * 100,
            height: (r.height / pageRect.height) * 100,
            pageNumber,
          });
        }
      }
    } catch {
      // Range API error → fall back to full span rect
      const rect = span.element.getBoundingClientRect();
      if (rect.width > 1 && rect.height > 1) {
        rects.push({
          top: ((rect.top - pageRect.top) / pageRect.height) * 100,
          left: ((rect.left - pageRect.left) / pageRect.width) * 100,
          width: (rect.width / pageRect.width) * 100,
          height: (rect.height / pageRect.height) * 100,
          pageNumber,
        });
      }
    }
  }

  return rects;
}

/**
 * Merge adjacent rects on the same line to reduce visual clutter.
 * Two rects are "same line" if their tops and heights are within 0.5%.
 */
function mergeAdjacentRects(rects: HighlightRect[]): HighlightRect[] {
  if (rects.length <= 1) return rects;

  const sorted = [...rects].sort((a, b) => a.top - b.top || a.left - b.left);
  const merged: HighlightRect[] = [sorted[0]];

  for (let i = 1; i < sorted.length; i++) {
    const prev = merged[merged.length - 1];
    const curr = sorted[i];

    const sameLine =
      Math.abs(prev.top - curr.top) < 0.5 &&
      Math.abs(prev.height - curr.height) < 0.5;

    // Adjacent if gap < 1%
    const adjacent = sameLine && curr.left <= prev.left + prev.width + 1;

    if (adjacent) {
      const newRight = Math.max(prev.left + prev.width, curr.left + curr.width);
      prev.width = newRight - prev.left;
    } else {
      merged.push({ ...curr });
    }
  }

  return merged;
}

/**
 * Find the text layer element within a page wrapper, and check whether
 * it has leaf <span> elements with text content.
 */
function findReadyTextLayer(pageWrapperEl: HTMLElement): HTMLElement | null {
  const textLayer = pageWrapperEl.querySelector(TEXT_LAYER_SELECTOR);
  if (!(textLayer instanceof HTMLElement)) return null;

  const spans = textLayer.querySelectorAll("span");
  for (const s of spans) {
    if (!s.querySelector("span") && (s.textContent ?? "").length > 0) {
      return textLayer; // has at least one leaf span with text
    }
  }
  return null;
}

/**
 * Wait for the text layer within a page wrapper to be populated with
 * span elements, then call `callback` with the text layer element.
 *
 * react-pdf fires `onRenderTextLayerSuccess` before the PDF.js text layer
 * has finished populating its <span> children. Additionally, React may
 * re-render and replace the text layer element between callbacks. To handle
 * both issues, we:
 *   1. Observe the page wrapper (which is stable, held by a ref) for
 *      subtree mutations.
 *   2. Re-query the text layer fresh each time we check.
 *   3. Pass the freshly-queried element to the callback.
 */
function waitForTextLayer(
  pageWrapperEl: HTMLElement,
  callback: (textLayerEl: HTMLElement) => void,
): void {
  // Fast path: text layer is already populated
  const ready = findReadyTextLayer(pageWrapperEl);
  if (ready) {
    requestAnimationFrame(() => {
      // Re-query to survive any React re-render during the rAF gap
      const fresh = findReadyTextLayer(pageWrapperEl);
      if (fresh) callback(fresh);
    });
    return;
  }

  let settled = false;

  const settle = () => {
    if (settled) return;
    settled = true;
    observer.disconnect();
    clearTimeout(timer);
    // Re-query after one more frame for layout stability
    requestAnimationFrame(() => {
      const fresh = findReadyTextLayer(pageWrapperEl);
      if (fresh) {
        callback(fresh);
      }
      // If still no text layer, silently give up (no fallback for
      // this edge case — the page is likely not rendered).
    });
  };

  // Watch the page wrapper subtree for additions (text layer + spans)
  const observer = new MutationObserver(() => {
    if (findReadyTextLayer(pageWrapperEl)) {
      settle();
    }
  });

  observer.observe(pageWrapperEl, { childList: true, subtree: true });

  // Safety timeout
  const timer = setTimeout(settle, MAX_SPAN_WAIT_MS);
}

// ─── Hook ──────────────────────────────────────────────────────────────────

export function useClaimHighlights(claims: Claim[]): UseClaimHighlightsReturn {
  const [cache, setCache] = useState<HighlightCache>({});
  const [isComputing, setIsComputing] = useState(false);
  const claimsRef = useRef<Claim[]>(claims);
  const computedPagesRef = useRef<Set<number>>(new Set());

  // Reset when the claims array changes identity
  useEffect(() => {
    const ids = claims.map((c) => c.id).sort().join(",");
    const prev = claimsRef.current.map((c) => c.id).sort().join(",");
    if (ids !== prev) {
      claimsRef.current = claims;
      computedPagesRef.current = new Set();
      setCache({});
    }
  }, [claims]);

  // ── computeHighlights ──────────────────────────────────────────────
  const computeHighlights = useCallback(
    (pageNumber: number, pageWrapperEl: HTMLElement) => {
      if (computedPagesRef.current.has(pageNumber)) return;

      const pageClaims = claims.filter((c) => c.source_page === pageNumber);
      if (pageClaims.length === 0) {
        computedPagesRef.current.add(pageNumber);
        return;
      }

      setIsComputing(true);

      // Wait for the text layer to be populated with span elements.
      // react-pdf's onRenderTextLayerSuccess fires before PDF.js finishes
      // populating the <span> children. Additionally, React may replace
      // the text layer element between callbacks (e.g. when setCache
      // triggers a re-render for another page). We pass the page wrapper
      // (held by a stable ref) and re-query the text layer fresh.
      waitForTextLayer(pageWrapperEl, (textLayerEl) => {
        const pageRect = textLayerEl.getBoundingClientRect();
        if (pageRect.width === 0 || pageRect.height === 0) {
          setIsComputing(false);
          return;
        }

        // ── Build span index (the key data structure) ──────────────
        const { spans, rawText } = buildSpanIndex(textLayerEl);
        const normText = normalize(rawText);
        const normToRaw = buildNormToRawMap(rawText);

        const highlights: ClaimHighlightData[] = [];

        for (let ci = 0; ci < pageClaims.length; ci++) {
          const claim = pageClaims[ci];
          let matched = false;
          let rects: HighlightRect[] = [];

          // Candidates: most specific → least specific
          const candidates: string[] = [
            claim.claim_text,
            claim.claim_text.length > 60 ? claim.claim_text.slice(0, 60) : "",
            claim.source_location?.source_context ?? "",
          ].filter(Boolean);

          for (const candidate of candidates) {
            const normNeedle = normalize(candidate);
            if (normNeedle.length < 10) continue;

            const normIdx = normText.indexOf(normNeedle);
            if (normIdx === -1) continue;

            // Map normalized match range → raw concatenated string range
            const rawStart = normToRaw[normIdx]?.rawIndex;
            const normEndIdx = Math.min(
              normIdx + normNeedle.length - 1,
              normToRaw.length - 1,
            );
            const rawEnd = normToRaw[normEndIdx]?.rawIndex;
            if (rawStart === undefined || rawEnd === undefined) continue;

            const matchStart = rawStart;
            const matchEnd = rawEnd + 1; // exclusive

            // ── Get rects span-by-span (no cross-span Ranges) ──────
            const rawRects = getRectsFromSpans(
              spans,
              matchStart,
              matchEnd,
              pageRect,
              pageNumber,
            );

            if (rawRects.length > 0) {
              rects = mergeAdjacentRects(rawRects);
              matched = true;
              break;
            }
          }

          // Fallback: stagger unmatched claims vertically
          if (!matched) {
            rects = [
              {
                top: 8 + ci * 6,
                left: 5,
                width: 90,
                height: 2.5,
                pageNumber,
              },
            ];
          }

          highlights.push({ claim, rects, matched });
        }

        computedPagesRef.current.add(pageNumber);
        setCache((prev) => ({ ...prev, [pageNumber]: highlights }));
        setIsComputing(false);
      });
    },
    [claims],
  );

  // ── getHighlightsForPage ────────────────────────────────────────────
  const getHighlightsForPage = useCallback(
    (pageNumber: number): ClaimHighlightData[] => {
      if (cache[pageNumber]) return cache[pageNumber];
      return [];
    },
    [cache],
  );

  // ── matchRate ───────────────────────────────────────────────────────
  const matchRate = useMemo(() => {
    const all = Object.values(cache).flat();
    if (all.length === 0) return 100;
    const matched = all.filter((h) => h.matched).length;
    return Math.round((matched / all.length) * 100);
  }, [cache]);

  return { getHighlightsForPage, computeHighlights, isComputing, matchRate };
}
