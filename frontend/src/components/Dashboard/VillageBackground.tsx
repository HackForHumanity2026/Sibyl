/**
 * VillageBackground — Subtle warm SVG village decorations rendered behind the graph.
 * Includes huts, trees, a winding path, and a fence segment at ~10% opacity.
 * All elements are decorative only — pointer-events: none.
 */

export function VillageBackground() {
  return (
    <div
      className="village-bg"
      aria-hidden="true"
      style={{ pointerEvents: "none" }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1400 700"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
        style={{ opacity: 0.11 }}
      >
        {/* ── Winding path connecting left to right ── */}
        <path
          d="M 0 420 Q 200 380 400 440 Q 600 500 800 430 Q 1000 360 1200 420 Q 1300 450 1400 400"
          fill="none"
          stroke="#a08060"
          strokeWidth="14"
          strokeDasharray="1 0"
          strokeLinecap="round"
          opacity={0.5}
        />

        {/* ── Hut 1 — left side ── */}
        <g transform="translate(60, 280)">
          {/* Walls */}
          <rect x="0" y="40" width="80" height="55" rx="2" fill="#c8a97a" />
          {/* Roof */}
          <polygon points="−8,42 40,0 88,42" fill="#a08060" />
          {/* Door */}
          <rect x="30" y="65" width="20" height="30" rx="3" fill="#8b6f4a" />
          {/* Window */}
          <rect x="8" y="52" width="18" height="15" rx="2" fill="#8b6f4a" />
          <line x1="17" y1="52" x2="17" y2="67" stroke="#a08060" strokeWidth="1.5" />
          <line x1="8" y1="59.5" x2="26" y2="59.5" stroke="#a08060" strokeWidth="1.5" />
          {/* Chimney */}
          <rect x="54" y="12" width="12" height="22" rx="1" fill="#a08060" />
          {/* Smoke puffs */}
          <circle cx="60" cy="8" r="5" fill="#c8a97a" opacity={0.6} />
          <circle cx="55" cy="2" r="4" fill="#c8a97a" opacity={0.4} />
        </g>

        {/* ── Tree 1 — behind hut left ── */}
        <g transform="translate(165, 290)">
          {/* Trunk */}
          <rect x="10" y="45" width="10" height="30" rx="2" fill="#a08060" />
          {/* Canopy layers */}
          <ellipse cx="15" cy="38" rx="22" ry="18" fill="#a08060" />
          <ellipse cx="15" cy="26" rx="16" ry="13" fill="#a08060" opacity={0.8} />
          <ellipse cx="15" cy="16" rx="11" ry="10" fill="#a08060" opacity={0.6} />
        </g>

        {/* ── Hut 2 — right side, bigger ── */}
        <g transform="translate(1200, 240)">
          {/* Walls */}
          <rect x="0" y="50" width="100" height="70" rx="2" fill="#c8a97a" />
          {/* Roof */}
          <polygon points="−10,52 50,0 110,52" fill="#a08060" />
          {/* Door */}
          <rect x="38" y="80" width="24" height="40" rx="3" fill="#8b6f4a" />
          {/* Window L */}
          <rect x="8" y="62" width="22" height="18" rx="2" fill="#8b6f4a" />
          <line x1="19" y1="62" x2="19" y2="80" stroke="#a08060" strokeWidth="1.5" />
          <line x1="8" y1="71" x2="30" y2="71" stroke="#a08060" strokeWidth="1.5" />
          {/* Window R */}
          <rect x="70" y="62" width="22" height="18" rx="2" fill="#8b6f4a" />
          <line x1="81" y1="62" x2="81" y2="80" stroke="#a08060" strokeWidth="1.5" />
          <line x1="70" y1="71" x2="92" y2="71" stroke="#a08060" strokeWidth="1.5" />
          {/* Chimney */}
          <rect x="68" y="15" width="13" height="28" rx="1" fill="#a08060" />
          <circle cx="74" cy="10" r="6" fill="#c8a97a" opacity={0.6} />
          <circle cx="68" cy="3" r="4" fill="#c8a97a" opacity={0.4} />
        </g>

        {/* ── Tree 2 — behind hut right ── */}
        <g transform="translate(1130, 260)">
          <rect x="10" y="50" width="10" height="30" rx="2" fill="#a08060" />
          <ellipse cx="15" cy="42" rx="20" ry="16" fill="#a08060" />
          <ellipse cx="15" cy="30" rx="14" ry="11" fill="#a08060" opacity={0.8} />
          <ellipse cx="15" cy="20" rx="10" ry="9" fill="#a08060" opacity={0.6} />
        </g>

        {/* ── Small tree center-top ── */}
        <g transform="translate(670, 80)">
          <rect x="8" y="40" width="8" height="25" rx="2" fill="#a08060" />
          <ellipse cx="12" cy="34" rx="17" ry="14" fill="#a08060" />
          <ellipse cx="12" cy="23" rx="12" ry="10" fill="#a08060" opacity={0.8} />
        </g>

        {/* ── Fence segment — lower left ── */}
        <g transform="translate(155, 380)" stroke="#a08060" strokeWidth="2.5" fill="none">
          <line x1="0" y1="0" x2="0" y2="28" strokeLinecap="round" />
          <line x1="16" y1="0" x2="16" y2="28" strokeLinecap="round" />
          <line x1="32" y1="0" x2="32" y2="28" strokeLinecap="round" />
          <line x1="48" y1="0" x2="48" y2="28" strokeLinecap="round" />
          <line x1="64" y1="0" x2="64" y2="28" strokeLinecap="round" />
          <line x1="-3" y1="8" x2="67" y2="8" strokeLinecap="round" />
          <line x1="-3" y1="20" x2="67" y2="20" strokeLinecap="round" />
        </g>

        {/* ── Fence segment — lower right ── */}
        <g transform="translate(1110, 370)" stroke="#a08060" strokeWidth="2.5" fill="none">
          <line x1="0" y1="0" x2="0" y2="28" strokeLinecap="round" />
          <line x1="16" y1="0" x2="16" y2="28" strokeLinecap="round" />
          <line x1="32" y1="0" x2="32" y2="28" strokeLinecap="round" />
          <line x1="48" y1="0" x2="48" y2="28" strokeLinecap="round" />
          <line x1="-3" y1="8" x2="52" y2="8" strokeLinecap="round" />
          <line x1="-3" y1="20" x2="52" y2="20" strokeLinecap="round" />
        </g>

        {/* ── Small bushes ── */}
        <ellipse cx="340" cy="500" rx="28" ry="16" fill="#a08060" opacity={0.6} />
        <ellipse cx="370" cy="492" rx="20" ry="13" fill="#a08060" opacity={0.5} />
        <ellipse cx="1020" cy="480" rx="26" ry="15" fill="#a08060" opacity={0.6} />
        <ellipse cx="1048" cy="472" rx="18" ry="12" fill="#a08060" opacity={0.5} />

        {/* ── Stepping stones along path ── */}
        {[150, 320, 510, 700, 890, 1080, 1260].map((x, i) => (
          <ellipse
            key={i}
            cx={x}
            cy={420 + Math.sin(i * 0.9) * 18}
            rx="14"
            ry="7"
            fill="#c8a97a"
            opacity={0.4}
          />
        ))}
      </svg>
    </div>
  );
}
