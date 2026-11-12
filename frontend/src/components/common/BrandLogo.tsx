import React, { useState } from "react";
import { motion } from "framer-motion";
import { Sprout } from "lucide-react";

interface BrandLogoProps {
  size?: "sm" | "md" | "lg";
  animateEntrance?: boolean;
  className?: string;
}

const SIZE_CLASSES: Record<NonNullable<BrandLogoProps["size"]>, string> = {
  sm: "h-9 w-auto max-w-[150px]",
  md: "h-12 w-auto max-w-[200px]",
  lg: "h-24 sm:h-28 w-auto max-w-[320px]",
};

/**
 * Displays the supplied /assets/raithamitra-logo.png image untouched.
 * If the PNG has not yet been placed into frontend/public/assets/,
 * renders a neutral temporary placeholder without redesigning the brand logo.
 */
export const BrandLogo: React.FC<BrandLogoProps> = ({
  size = "md",
  animateEntrance = false,
  className = "",
}) => {
  const [missing, setMissing] = useState(false);

  const leafVariants = {
    hidden: { scale: 0.4, opacity: 0, rotate: -12 },
    visible: (delay: number) => ({
      scale: 1,
      opacity: 1,
      rotate: 0,
      transition: { duration: 0.7, delay, ease: "easeOut" },
    }),
  };

  return (
    <motion.div
      initial={animateEntrance ? { opacity: 0, y: 10 } : false}
      animate={animateEntrance ? { opacity: 1, y: 0 } : undefined}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`inline-flex items-center gap-2 ${className}`}
    >
      {animateEntrance && (
        <motion.span
          custom={0.15}
          initial="hidden"
          animate="visible"
          variants={leafVariants}
          aria-hidden="true"
          className="hidden sm:inline-flex h-8 w-8 items-center justify-center rounded-full bg-mint text-leaf"
        >
          <Sprout className="h-4 w-4" />
        </motion.span>
      )}

      {!missing ? (
        <img
          src="/assets/raithamitra-logo.png"
          alt="Raitha Mitra — Your Smart Farming Companion"
          onError={() => setMissing(true)}
          className={`${SIZE_CLASSES[size]} object-contain select-none`}
        />
      ) : (
        <div
          className="inline-flex items-center gap-2 rounded-xl border border-dashed border-muted/40 bg-cream px-3 py-1.5 text-left"
          title="Place original raithamitra-logo.png in frontend/public/assets/"
        >
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-deep">Raitha Mitra</span>
            <span className="text-[11px] text-muted">
              {size === "lg"
                ? "Logo slot: /assets/raithamitra-logo.png"
                : "Your Smart Farming Companion"}
            </span>
          </div>
        </div>
      )}

      {animateEntrance && (
        <motion.span
          custom={0.3}
          initial="hidden"
          animate="visible"
          variants={leafVariants}
          aria-hidden="true"
          className="hidden sm:inline-flex h-7 w-7 items-center justify-center rounded-full bg-mint text-forest"
        >
          <Sprout className="h-3.5 w-3.5" />
        </motion.span>
      )}
    </motion.div>
  );
};
