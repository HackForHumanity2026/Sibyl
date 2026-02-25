# Sibyl Design System

> This document is the single source of truth for all UI/UX design decisions in the Sibyl frontend. All new components and modifications must comply with these principles.

---

## Core Principles

### 1. Warm Cream Color Palette
- **Background**: `#fff6e9` (warm off-white cream) as the default for all pages and surfaces
- **Text hierarchy** uses warm browns, never cold greys:
  - **Primary text**: `text-slate-900` or `#2d241a` (near-black warm)
  - **Body text**: `text-[#4a3c2e]` (dark warm brown)
  - **Labels**: `text-[#6b5344]` (medium warm brown)
  - **Muted/hints**: `text-[#8b7355]` (light warm brown)
- **Muted surfaces**: `#eddfc8` (warm tan) — NOT cold `#f5f5f5`
- **Borders** (when needed): `#e0d4bf` (warm cream border)
- **Semantic colors** are the **only** permitted accent colors:
  - **Verified** → `emerald-500` / `green-500`
  - **Contradicted** → `rose-500` / `red-500`
  - **Unverified / Insufficient Evidence** → `amber-500` / `yellow-500`
  - **Disclosure Gaps** → `amber-400`
- **Never use cold greys** (`slate-400`, `slate-500`, `slate-600`) — always warm browns.

### 2. Light Theme is Default
- The `:root` CSS variables always define the light theme.
- Dark mode is a secondary concern and must never be the default in the codebase.
- Do NOT apply the `.dark` class to `<html>` or `<body>` by default.

### 3. Icons Only — No Emojis
- **Lucide React** is the exclusive icon library for the entire application.
- Emojis are strictly banned from all source files, including JSX, TypeScript constants, and inline strings.
- All icon usage must import from `lucide-react`. No raw SVGs in component files unless absolutely necessary.
- Icon sizes: `16` (inline/small), `20` (standard), `24` (prominent/heading-level).

### 4. Horizontal Top Navigation
- Navigation lives in a single horizontal bar at the top of every page.
- No vertical sidebars.
- Structure: `[Logo] [Nav Links...] [Utility Actions]`
- Nav links use text labels only (no icons in the navbar).
- Active state: bottom border underline or background highlight — never heavy colored fills.

### 5. Visual Hierarchy
- Every screen must have a clear primary metric or action.
- Primary content: large type, full contrast.
- Secondary content: smaller type, muted foreground (`text-muted-foreground`).
- Tertiary/metadata: extra small type, low contrast.
- Never treat all metrics as equal — guide the user's eye.

### 6. Minimal Layout & Containers
- Max content width: `max-w-6xl` (1152px) — avoid full-bleed text on wide screens.
- Page padding: `px-6 py-8` standard.
- **No container borders** — use negative space (whitespace/padding) to separate elements.
- **No rounded corners on content cards** — flat edges, no `rounded-xl` on claim/gap cards.
- **Shadows sparingly** — only `shadow-sm` on elevated elements (modals, popovers).
- Consistent spacing scale: use Tailwind spacing (`space-y-4`, `gap-6`, etc.).
- Cards blend into background — separation via spacing, not outlines.

---

## Color Reference

| Token | Value | Use |
|-------|-------|-----|
| `--background` | `#fff6e9` | Page background (warm cream) |
| `--foreground` | `#0f0f0f` | Primary text |
| `--card` | `#fff6e9` | Card backgrounds |
| `--muted` | `#eddfc8` | Subtle/hover backgrounds |
| `--muted-foreground` | `#6b5344` | Secondary / helper text |
| `--border` | `#e0d4bf` | Borders, dividers |
| `--primary` | `#0f0f0f` | CTAs, active nav states |
| Body text | `#4a3c2e` | Readable body copy |
| Labels | `#6b5344` | Form labels, metadata |
| Muted | `#8b7355` | Hints, placeholders |
| `emerald-500` | `#10b981` | Verified verdict |
| `rose-500` | `#f43f5e` | Contradicted verdict |
| `amber-500` | `#f59e0b` | Unverified / Insufficient |
| `amber-400` | `#fbbf24` | Disclosure gaps |

---

## Typography

| Usage | Class |
|-------|-------|
| Page title (H1) | `text-2xl font-bold text-foreground` |
| Section heading (H2) | `text-lg font-semibold text-foreground` |
| Card/group heading (H3) | `text-base font-semibold text-foreground` |
| Body text | `text-sm text-foreground` |
| Helper / secondary text | `text-sm text-muted-foreground` |
| Metadata / micro text | `text-xs text-muted-foreground` |
| Monospace / code | `font-mono text-xs` |

---

## Icon Usage (Lucide React)

### Pillar Icons
| Pillar | Icon Component | Import |
|--------|---------------|--------|
| Governance | `Building2` | `lucide-react` |
| Strategy | `Target` | `lucide-react` |
| Risk Management | `AlertTriangle` | `lucide-react` |
| Metrics & Targets | `BarChart3` | `lucide-react` |

### Common UI Icons
| Context | Icon |
|---------|------|
| Loading spinner | `Loader2` (with `animate-spin`) |
| Error state | `AlertCircle` |
| Document / file | `FileText` |
| External link | `ExternalLink` |
| Search | `Search` |
| Filter | `Filter` |
| Chevron (expand/collapse) | `ChevronDown`, `ChevronRight` |
| Back/navigation | `ArrowLeft` |
| Refresh | `RefreshCw` |
| Verified check | `CheckCircle2` |
| Contradicted X | `XCircle` |
| Unverified question | `HelpCircle` |
| Dev-mode / quick action | `Zap` |
| Close | `X` |

---

## Navigation Structure

```
+---------------------------------------------------------------+
|  [S] Sibyl       Home    Analysis    Report         [utility] |
+---------------------------------------------------------------+
|                                                               |
|                     Page Content                              |
|                                                               |
+---------------------------------------------------------------+
```

- Logo: branded mark `[S]` + wordmark "Sibyl" — links to `/`
- Nav links: plain text, no icon prefix
- Active link: `font-medium` + bottom border underline using `border-b-2 border-foreground`
- Inactive link: `text-muted-foreground hover:text-foreground`

---

## Report Screen Layout

### Compliance Summary Visual Hierarchy

The Compliance Summary card uses a deliberate hierarchy:

1. **Hero metric** (primary): Verified Percentage — oversized, full contrast
2. **Supporting metrics** (secondary): Total Claims, Contradicted, Disclosure Gaps — smaller, below the hero
3. **Verdict distribution bar** (tertiary): animated progress bar with legend
4. **Pillar coverage grid** (quaternary): mini progress bars per pillar

This hierarchy ensures the user immediately understands the compliance health score (verified %), then can drill down into specifics.

### Card Styling Convention
```css
/* Standard content block — no border, no rounding */
bg-[#fff6e9] p-5

/* Elevated panel (modals, popovers only) */
bg-[#fff6e9] shadow-lg rounded-xl p-6

/* Interactive/hover surfaces */
bg-[#f5ecdb] hover:bg-[#eddfc8]
```
Cards blend seamlessly into the page — separation comes from **spacing**, not outlines.

---

## Component Conventions

### Badges / Tags
- **Verdict badge**: rounded-full, semantic background at 10-15% opacity, semantic text color, small border
- **Type badge**: rounded, muted background, muted text — not colored
- **Priority badge**: small, uses semantic color at low opacity

### Buttons
- **Primary**: `bg-primary text-primary-foreground hover:bg-primary/90`
- **Secondary / Ghost**: `border border-border text-muted-foreground hover:bg-muted`
- **Destructive**: `bg-destructive text-white`
- All buttons: `rounded-md`, `text-sm font-medium`, `px-4 py-2`

### Filter Controls
- Use `<select>` or pill-style chip buttons
- Active filter chip: `bg-slate-900 text-white`
- Inactive: `bg-white border border-slate-200 text-slate-600`

### Evidence Chain
- Collapsed by default
- Expand trigger at bottom of card with `ChevronDown` icon
- Smooth height animation on expand/collapse

### Chatbot Messages
- **User messages**: dark bubble (`bg-slate-900 text-white`) with slight border-radius
- **AI messages**: **no bubble** — plain text directly on background, minimal styling
- Citations are inline numbered buttons, tappable to scroll PDF

---

## Prohibited Patterns

| Pattern | Reason |
|---------|--------|
| Emojis in any source file | Inconsistent rendering, unprofessional |
| Dark theme as default | Violates light-first principle |
| Cold grey text (`slate-400/500/600`) | Violates warm palette — use `#8b7355`, `#6b5344`, `#4a3c2e` |
| Container borders (`border border-slate-200`) | Violates minimal container rule — use spacing instead |
| Rounded corners on content cards | Flat cards only — save rounding for modals/badges |
| AI chat bubble backgrounds | AI text is plain, no bubble |
| Multiple accent colors in one view | Violates minimal color principle |
| Raw inline SVG in component files | Use Lucide imports instead |
| Vertical sidebar navigation | Replaced by horizontal top nav |
| Equal weight for all dashboard metrics | Use hierarchy to guide attention |

---

---

## Ecological Decoration Pattern

### Overview
The HomePage landing screen uses an animated leaf background to reinforce Sibyl's sustainability theme. This decorative layer is **exclusive to the HomePage** — it must not be added to any other page.

### Component
`frontend/src/components/LeafBackground.tsx`

- Renders 14 SVG leaf elements (oval, maple, willow, tropical shapes) positioned in corners and along edges
- All leaves are `position: fixed`, `z-index: 0`, `pointer-events: none`, so they never interfere with user interaction
- Page content must use `z-index: 10` or higher to sit above the leaf layer

### Colors
Only the following leaf colors are permitted:

| Token | Value | Tailwind equivalent |
|-------|-------|---------------------|
| Deep leaf | `#059669` | `emerald-600` |
| Mid leaf | `#34d399` | `emerald-400` |
| Light leaf | `#6ee7b7` | `emerald-300` |
| Pale leaf | `#a7f3d0` | `emerald-200` |

Leaf opacity must stay in the **7–15%** range. Never use opacity above 20% — it competes with content.

### Animation Spec (framer-motion)
| Property | Range | Duration | Easing |
|----------|-------|----------|--------|
| Rotation | ±6 degrees around initial angle | 4–8 s | ease-in-out |
| Translate Y | ±10–15 px | 5–8 s | ease-in-out |
| Scale | 0.95–1.05 | 6–10 s | ease-in-out |

All animations use `repeatType: "reverse"` with staggered durations so leaves move independently and never in sync.

### Layout Rule
In `HomePage.tsx`:
```jsx
<div className="relative ... overflow-hidden">
  <LeafBackground />           {/* fixed, z-0 */}
  <div className="relative z-10 ...">  {/* content above leaves */}
    {/* hero, upload widget, feature tiles */}
  </div>
</div>
```

---

## Versioning

| Date | Change |
|------|--------|
| 2026-02-24 | Initial design system created — horizontal nav, light theme, Lucide icons, report hierarchy |
| 2026-02-24 | Added ecological decoration pattern — animated leaf background for HomePage |
| 2026-02-25 | Warm cream palette (`#fff6e9`) — replaced cold greys with warm browns, no container borders, flat cards, no AI chat bubbles |
