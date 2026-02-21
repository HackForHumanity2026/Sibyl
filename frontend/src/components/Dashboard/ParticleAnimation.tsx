/**
 * ParticleAnimation - Animated particles flowing along edge paths.
 * Uses Framer Motion for smooth path-following animation.
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import type { EdgeVolume } from "@/types/dashboard";

interface ParticleAnimationProps {
  edgePath: string;
  volume: EdgeVolume;
  color: string;
  direction?: "forward" | "backward";
}

const VOLUME_PARTICLE_COUNT: Record<EdgeVolume, number> = {
  low: 3,
  medium: 6,
  high: 12,
};

export function ParticleAnimation({
  edgePath,
  volume,
  color,
  direction = "forward",
}: ParticleAnimationProps) {
  const particleCount = VOLUME_PARTICLE_COUNT[volume];

  const particles = useMemo(
    () =>
      Array.from({ length: particleCount }, (_, i) => ({
        id: i,
        offset: (i / particleCount) * 100,
        duration: 2 + Math.random() * 0.5,
        delay: (i / particleCount) * 2,
      })),
    [particleCount]
  );

  return (
    <g className="particle-animation">
      {particles.map((particle) => (
        <motion.circle
          key={particle.id}
          r={3}
          fill={color}
          style={{
            offsetPath: `path("${edgePath}")`,
            offsetRotate: "0deg",
          }}
          initial={{
            offsetDistance: direction === "forward" ? "0%" : "100%",
            opacity: 0,
          }}
          animate={{
            offsetDistance: direction === "forward" ? "100%" : "0%",
            opacity: [0, 0.8, 0.8, 0],
          }}
          transition={{
            duration: particle.duration,
            delay: particle.delay,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
    </g>
  );
}
