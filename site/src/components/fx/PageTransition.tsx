"use client";

import { motion, useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/** Fade/scale/blur-in on every route change. */
export default function PageTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const reduce = useReducedMotion();
  return (
    <motion.main
      key={pathname}
      initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.96, filter: "blur(8px) hue-rotate(90deg)" }}
      animate={
        reduce
          ? { opacity: 1 }
          : {
              opacity: 1,
              scale: 1,
              filter: "blur(0px) hue-rotate(0deg)",
              // drop filter/transform after so fixed-position children aren't trapped
              transitionEnd: { filter: "none", transform: "none" },
            }
      }
      transition={{ duration: reduce ? 0.15 : 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="relative flex-1"
    >
      {children}
    </motion.main>
  );
}
