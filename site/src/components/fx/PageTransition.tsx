"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/**
 * Fade/slide-in on every route change. Pure CSS (opacity + transform only), so it
 * runs before hydration, never leaves the page stuck hidden or blurred, and stays
 * on the compositor.
 */
export default function PageTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <main key={pathname} className="fx-page-in relative flex-1">
      {children}
    </main>
  );
}
