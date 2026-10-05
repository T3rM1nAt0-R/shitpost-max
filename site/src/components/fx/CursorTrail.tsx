"use client";

import { useEffect, useRef } from "react";

const GLYPHS = ["✨", "💸", "💎", "🚀", "⭐", "💰", "🔥"];

/** Emoji/sparkle trail that follows the cursor. Disabled on touch and reduced motion. */
export default function CursorTrail() {
  const layer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = layer.current;
    if (!root) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia("(pointer: fine)").matches) return;

    let last = 0;
    let live = 0;
    const onMove = (e: PointerEvent) => {
      const now = performance.now();
      if (now - last < 28 || live > 40) return;
      last = now;
      live++;
      const el = document.createElement("span");
      el.className = "fx-trail";
      el.textContent = GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
      el.style.left = `${e.clientX}px`;
      el.style.top = `${e.clientY}px`;
      el.style.setProperty("--dx", `${(Math.random() - 0.5) * 60}px`);
      el.style.setProperty("--rot", `${(Math.random() - 0.5) * 120}deg`);
      el.addEventListener(
        "animationend",
        () => {
          el.remove();
          live--;
        },
        { once: true },
      );
      root.appendChild(el);
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      root.replaceChildren();
    };
  }, []);

  return (
    <div
      ref={layer}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-[60] overflow-hidden"
    />
  );
}
