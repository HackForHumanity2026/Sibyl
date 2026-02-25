/**
 * LeafBackground — decorative animated leaf overlay.
 * Large semi-transparent SVG leaves "come out" of screen corners with
 * gentle wind-like motion using framer-motion.
 *
 * Design: ecological theme, emerald palette at low opacity.
 * Exclusive to the HomePage (per design-system.md).
 */

import { motion } from "framer-motion";

// ============================================================================
// SVG Leaf Shapes
// ============================================================================

const OvalLeaf = ({ color = "#34d399" }: { color?: string }) => (
  <svg viewBox="0 0 60 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M30 3 C58 18 60 58 30 97 C0 58 2 18 30 3Z" fill={color} />
    <path d="M30 6 L30 94" stroke="white" strokeWidth="1.8" strokeLinecap="round" opacity="0.45" />
    <path d="M30 28 C20 26 12 21 10 14" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.3" />
    <path d="M30 44 C18 42 10 36 7 27" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.3" />
    <path d="M30 60 C19 57 12 50 9 41" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.3" />
    <path d="M30 28 C40 26 48 21 50 14" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.3" />
    <path d="M30 44 C42 42 50 36 53 27" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.3" />
    <path d="M30 60 C41 57 48 50 51 41" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.3" />
  </svg>
);

const MapleLeaf = ({ color = "#34d399" }: { color?: string }) => (
  <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M50 4
         C50 4 42 20 32 22
         C20 24 8 16 6 24
         C4 33 16 38 20 44
         C12 49 2 52 4 62
         C6 72 20 67 26 69
         C28 78 26 90 33 92
         C40 94 47 82 50 79
         C53 82 60 94 67 92
         C74 90 72 78 74 69
         C80 67 94 72 96 62
         C98 52 88 49 80 44
         C84 38 96 33 94 24
         C92 16 80 24 68 22
         C58 20 50 4 50 4Z"
      fill={color}
    />
    <path d="M50 22 L50 90" stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
    <path d="M50 42 L28 34" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.28" />
    <path d="M50 54 L18 48" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.28" />
    <path d="M50 42 L72 34" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.28" />
    <path d="M50 54 L82 48" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.28" />
  </svg>
);

const WillowLeaf = ({ color = "#34d399" }: { color?: string }) => (
  <svg viewBox="0 0 28 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 2 C26 28 28 68 14 118 C0 68 2 28 14 2Z" fill={color} />
    <path d="M14 4 L14 116" stroke="white" strokeWidth="1.4" strokeLinecap="round" opacity="0.45" />
    <path d="M14 30 C9 28 5 23 4 17" stroke="white" strokeWidth="0.9" strokeLinecap="round" opacity="0.32" />
    <path d="M14 52 C8 49 4 43 3 35" stroke="white" strokeWidth="0.9" strokeLinecap="round" opacity="0.32" />
    <path d="M14 30 C19 28 23 23 24 17" stroke="white" strokeWidth="0.9" strokeLinecap="round" opacity="0.32" />
    <path d="M14 52 C20 49 24 43 25 35" stroke="white" strokeWidth="0.9" strokeLinecap="round" opacity="0.32" />
  </svg>
);

const TropicalLeaf = ({ color = "#34d399" }: { color?: string }) => (
  <svg viewBox="0 0 120 90" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M60 82 C12 82 2 52 5 28 C8 6 28 0 60 2 C92 0 112 6 115 28 C118 52 108 82 60 82Z"
      fill={color}
    />
    <path d="M60 80 L60 8" stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
    <path d="M60 38 C46 32 30 30 16 33" stroke="white" strokeWidth="1.3" strokeLinecap="round" opacity="0.28" />
    <path d="M60 54 C43 48 25 47 10 52" stroke="white" strokeWidth="1.3" strokeLinecap="round" opacity="0.28" />
    <path d="M60 38 C74 32 90 30 104 33" stroke="white" strokeWidth="1.3" strokeLinecap="round" opacity="0.28" />
    <path d="M60 54 C77 48 95 47 110 52" stroke="white" strokeWidth="1.3" strokeLinecap="round" opacity="0.28" />
  </svg>
);

const FernLeaf = ({ color = "#34d399" }: { color?: string }) => (
  <svg viewBox="0 0 80 160" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Stem */}
    <path d="M40 155 L40 10" stroke={color} strokeWidth="3" strokeLinecap="round" />
    {/* Left fronds */}
    <path d="M40 30 C30 26 18 28 10 24" stroke={color} strokeWidth="8" strokeLinecap="round" opacity="0.8" />
    <path d="M40 48 C26 42 14 44 4 38" stroke={color} strokeWidth="9" strokeLinecap="round" opacity="0.8" />
    <path d="M40 66 C24 59 12 62 2 55" stroke={color} strokeWidth="9" strokeLinecap="round" opacity="0.8" />
    <path d="M40 84 C26 77 14 80 4 73" stroke={color} strokeWidth="8" strokeLinecap="round" opacity="0.8" />
    <path d="M40 102 C28 96 18 98 10 93" stroke={color} strokeWidth="7" strokeLinecap="round" opacity="0.8" />
    <path d="M40 118 C30 113 22 115 16 110" stroke={color} strokeWidth="6" strokeLinecap="round" opacity="0.8" />
    <path d="M40 132 C33 128 27 130 23 126" stroke={color} strokeWidth="5" strokeLinecap="round" opacity="0.7" />
    {/* Right fronds */}
    <path d="M40 30 C50 26 62 28 70 24" stroke={color} strokeWidth="8" strokeLinecap="round" opacity="0.8" />
    <path d="M40 48 C54 42 66 44 76 38" stroke={color} strokeWidth="9" strokeLinecap="round" opacity="0.8" />
    <path d="M40 66 C56 59 68 62 78 55" stroke={color} strokeWidth="9" strokeLinecap="round" opacity="0.8" />
    <path d="M40 84 C54 77 66 80 76 73" stroke={color} strokeWidth="8" strokeLinecap="round" opacity="0.8" />
    <path d="M40 102 C52 96 62 98 70 93" stroke={color} strokeWidth="7" strokeLinecap="round" opacity="0.8" />
    <path d="M40 118 C50 113 58 115 64 110" stroke={color} strokeWidth="6" strokeLinecap="round" opacity="0.8" />
    <path d="M40 132 C47 128 53 130 57 126" stroke={color} strokeWidth="5" strokeLinecap="round" opacity="0.7" />
  </svg>
);

// ============================================================================
// Leaf Configuration
// ============================================================================

type LeafType = "oval" | "maple" | "willow" | "tropical" | "fern";

interface LeafConfig {
  id: number;
  type: LeafType;
  style: React.CSSProperties;
  size: number;
  color: string;
  opacity: number;
  initialRotate: number;
  rotateRange: [number, number];
  yRange: [number, number];
  xRange: [number, number];
  duration: number;
  scaleRange: [number, number];
}

const C = {
  deep:  "#059669",
  mid:   "#10b981",
  light: "#34d399",
  pale:  "#6ee7b7",
};

const LEAVES: LeafConfig[] = [
  // ── TOP-LEFT: large cluster bursting from corner ──────────────────────────
  {
    id: 1,
    type: "maple",
    style: { top: "-220px", left: "-180px" },
    size: 520,
    color: C.mid,
    opacity: 0.14,
    initialRotate: 30,
    rotateRange: [24, 38],
    yRange: [-14, 14],
    xRange: [-6, 6],
    duration: 6.2,
    scaleRange: [0.97, 1.03],
  },
  {
    id: 2,
    type: "tropical",
    style: { top: "-60px", left: "-140px" },
    size: 380,
    color: C.light,
    opacity: 0.11,
    initialRotate: 55,
    rotateRange: [49, 63],
    yRange: [-18, 10],
    xRange: [-8, 8],
    duration: 7.4,
    scaleRange: [0.95, 1.05],
  },
  {
    id: 3,
    type: "fern",
    style: { top: "-40px", left: "-20px" },
    size: 260,
    color: C.deep,
    opacity: 0.10,
    initialRotate: 100,
    rotateRange: [94, 108],
    yRange: [-10, 12],
    xRange: [-4, 4],
    duration: 5.5,
    scaleRange: [0.96, 1.04],
  },
  {
    id: 4,
    type: "oval",
    style: { top: "80px", left: "-100px" },
    size: 200,
    color: C.pale,
    opacity: 0.09,
    initialRotate: 75,
    rotateRange: [68, 82],
    yRange: [-16, 8],
    xRange: [-6, 6],
    duration: 8.1,
    scaleRange: [0.96, 1.04],
  },

  // ── TOP-RIGHT: mirror cluster ─────────────────────────────────────────────
  {
    id: 5,
    type: "maple",
    style: { top: "-200px", right: "-160px" },
    size: 500,
    color: C.mid,
    opacity: 0.13,
    initialRotate: -35,
    rotateRange: [-42, -28],
    yRange: [-12, 16],
    xRange: [-6, 6],
    duration: 6.8,
    scaleRange: [0.97, 1.03],
  },
  {
    id: 6,
    type: "fern",
    style: { top: "-50px", right: "-30px" },
    size: 300,
    color: C.light,
    opacity: 0.11,
    initialRotate: -90,
    rotateRange: [-97, -83],
    yRange: [-14, 10],
    xRange: [-5, 5],
    duration: 5.9,
    scaleRange: [0.96, 1.04],
  },
  {
    id: 7,
    type: "oval",
    style: { top: "60px", right: "-80px" },
    size: 220,
    color: C.deep,
    opacity: 0.09,
    initialRotate: -125,
    rotateRange: [-132, -118],
    yRange: [-10, 14],
    xRange: [-4, 4],
    duration: 7.7,
    scaleRange: [0.97, 1.03],
  },
  {
    id: 8,
    type: "willow",
    style: { top: "160px", right: "-60px" },
    size: 180,
    color: C.pale,
    opacity: 0.08,
    initialRotate: -60,
    rotateRange: [-67, -53],
    yRange: [-12, 10],
    xRange: [-4, 4],
    duration: 6.3,
    scaleRange: [0.96, 1.04],
  },

  // ── BOTTOM-LEFT: cluster growing up from corner ───────────────────────────
  {
    id: 9,
    type: "tropical",
    style: { bottom: "-180px", left: "-140px" },
    size: 460,
    color: C.mid,
    opacity: 0.13,
    initialRotate: -25,
    rotateRange: [-32, -18],
    yRange: [-14, 10],
    xRange: [-6, 6],
    duration: 7.0,
    scaleRange: [0.96, 1.04],
  },
  {
    id: 10,
    type: "fern",
    style: { bottom: "-30px", left: "-10px" },
    size: 280,
    color: C.light,
    opacity: 0.10,
    initialRotate: -170,
    rotateRange: [-177, -163],
    yRange: [-10, 12],
    xRange: [-4, 4],
    duration: 5.7,
    scaleRange: [0.97, 1.03],
  },
  {
    id: 11,
    type: "oval",
    style: { bottom: "80px", left: "-70px" },
    size: 190,
    color: C.deep,
    opacity: 0.08,
    initialRotate: 145,
    rotateRange: [138, 152],
    yRange: [-12, 8],
    xRange: [-4, 4],
    duration: 8.4,
    scaleRange: [0.95, 1.05],
  },

  // ── BOTTOM-RIGHT: cluster ─────────────────────────────────────────────────
  {
    id: 12,
    type: "maple",
    style: { bottom: "-190px", right: "-160px" },
    size: 480,
    color: C.mid,
    opacity: 0.12,
    initialRotate: 155,
    rotateRange: [148, 162],
    yRange: [-10, 14],
    xRange: [-6, 6],
    duration: 6.5,
    scaleRange: [0.96, 1.04],
  },
  {
    id: 13,
    type: "fern",
    style: { bottom: "-20px", right: "-20px" },
    size: 270,
    color: C.light,
    opacity: 0.10,
    initialRotate: 80,
    rotateRange: [73, 87],
    yRange: [-10, 10],
    xRange: [-4, 4],
    duration: 6.1,
    scaleRange: [0.97, 1.03],
  },
  {
    id: 14,
    type: "willow",
    style: { bottom: "100px", right: "-50px" },
    size: 170,
    color: C.pale,
    opacity: 0.08,
    initialRotate: 20,
    rotateRange: [13, 27],
    yRange: [-14, 6],
    xRange: [-4, 4],
    duration: 7.2,
    scaleRange: [0.96, 1.04],
  },

  // ── MID-LEFT & MID-RIGHT edge accents ─────────────────────────────────────
  {
    id: 15,
    type: "willow",
    style: { top: "38%", left: "-80px" },
    size: 200,
    color: C.light,
    opacity: 0.08,
    initialRotate: 90,
    rotateRange: [83, 97],
    yRange: [-20, 20],
    xRange: [-4, 4],
    duration: 9.0,
    scaleRange: [0.96, 1.04],
  },
  {
    id: 16,
    type: "oval",
    style: { top: "45%", right: "-70px" },
    size: 180,
    color: C.pale,
    opacity: 0.07,
    initialRotate: -90,
    rotateRange: [-97, -83],
    yRange: [-18, 18],
    xRange: [-4, 4],
    duration: 8.6,
    scaleRange: [0.97, 1.03],
  },
];

// ============================================================================
// Single Animated Leaf
// ============================================================================

function AnimatedLeaf({ config }: { config: LeafConfig }) {
  const LeafMap = {
    oval:     OvalLeaf,
    maple:    MapleLeaf,
    willow:   WillowLeaf,
    tropical: TropicalLeaf,
    fern:     FernLeaf,
  };
  const LeafComponent = LeafMap[config.type];

  return (
    <motion.div
      style={{
        position: "absolute",
        width: config.size,
        opacity: config.opacity,
        transformOrigin: "center center",
        ...config.style,
      }}
      animate={{
        rotate: config.rotateRange,
        y:      config.yRange,
        x:      config.xRange,
        scale:  config.scaleRange,
      }}
      transition={{
        duration:   config.duration,
        repeat:     Infinity,
        repeatType: "reverse",
        ease:       "easeInOut",
      }}
      initial={{
        rotate: config.initialRotate,
        y: 0,
        x: 0,
        scale: 1,
      }}
    >
      <LeafComponent color={config.color} />
    </motion.div>
  );
}

// ============================================================================
// LeafBackground
// ============================================================================

export function LeafBackground() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        overflow: "hidden",
      }}
    >
      {LEAVES.map((leaf) => (
        <AnimatedLeaf key={leaf.id} config={leaf} />
      ))}
    </div>
  );
}
