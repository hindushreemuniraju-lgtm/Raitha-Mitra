import React from "react";
import { motion } from "framer-motion";

interface VoiceWaveformProps {
  active: boolean;
  mode: "idle" | "listening" | "speaking";
}

export const VoiceWaveform: React.FC<VoiceWaveformProps> = ({ active, mode }) => {
  const bars = [0.4, 0.75, 1.0, 0.65, 0.9, 0.55, 0.85, 0.5, 0.7];
  const colorClass =
    mode === "listening"
      ? "bg-leaf"
      : mode === "speaking"
      ? "bg-forest"
      : "bg-muted/30";

  return (
    <div className="flex items-center justify-center gap-1.5 h-12" aria-hidden="true">
      {bars.map((height, idx) => (
        <motion.span
          key={idx}
          animate={
            active
              ? {
                  scaleY: [0.35, height, 0.45, height * 0.85, 0.35],
                }
              : { scaleY: 0.25 }
          }
          transition={
            active
              ? {
                  duration: 0.9,
                  repeat: Infinity,
                  delay: idx * 0.08,
                  ease: "easeInOut",
                }
              : { duration: 0.2 }
          }
          className={`w-1.5 h-10 rounded-full origin-center ${colorClass}`}
        />
      ))}
    </div>
  );
};
