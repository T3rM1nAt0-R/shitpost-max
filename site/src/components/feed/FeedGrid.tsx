"use client";

import { useEffect, useRef, type MouseEvent, type PointerEvent, type ReactNode } from "react";
import { NEON } from "./neon";
import { useVotes } from "./votes";

const MAX_TILT = 18;

function restartClass(el: Element | null, cls: string) {
  if (!el) return;
  el.classList.remove(cls);
  void (el as HTMLElement).offsetWidth; // restart the CSS animation
  el.classList.add(cls);
  const done = (e: Event) => {
    if (e.target !== el) return; // ignore bubbling child animations
    el.classList.remove(cls);
    el.removeEventListener("animationend", done);
  };
  el.addEventListener("animationend", done);
}

/**
 * Grid wrapper for the server-rendered cards. One delegated set of listeners handles
 * tilt/glare (CSS vars, one rAF per frame), vote clicks and score text for all cards.
 */
export default function FeedGrid({ id, children }: { id: string; children: ReactNode }) {
  const [votes, vote] = useVotes();
  const ref = useRef<HTMLDivElement>(null);
  const hovered = useRef<HTMLElement | null>(null);
  const pending = useRef<{ x: number; y: number; card: HTMLElement } | null>(null);
  const raf = useRef(0);
  const shown = useRef<Record<string, number>>({});

  // Apply vote deltas to the static score text (only for slugs whose value changed).
  useEffect(() => {
    const grid = ref.current;
    if (!grid) return;
    const slugs = new Set([...Object.keys(votes), ...Object.keys(shown.current)]);
    for (const slug of slugs) {
      const delta = votes[slug] ?? 0;
      if ((shown.current[slug] ?? 0) === delta) continue;
      shown.current[slug] = delta;
      const card = grid.querySelector<HTMLElement>(`[data-slug="${CSS.escape(slug)}"]`);
      const scoreEl = card?.querySelector("[data-score]");
      if (!card || !scoreEl) continue;
      scoreEl.textContent = ((Number(card.dataset.baseScore) || 0) + delta).toLocaleString("en-US");
    }
  }, [votes]);

  useEffect(() => () => cancelAnimationFrame(raf.current), []);

  function reset(card: HTMLElement | null) {
    if (!card) return;
    card.style.removeProperty("--rx");
    card.style.removeProperty("--ry");
    card.style.removeProperty("--gx");
    card.style.removeProperty("--gy");
  }

  function flush() {
    raf.current = 0;
    const p = pending.current;
    pending.current = null;
    if (!p || p.card !== hovered.current) return;
    const r = p.card.getBoundingClientRect();
    const fx = Math.min(1, Math.max(0, (p.x - r.left) / r.width));
    const fy = Math.min(1, Math.max(0, (p.y - r.top) / r.height));
    const s = p.card.style;
    s.setProperty("--rx", `${((0.5 - fy) * 2 * MAX_TILT).toFixed(2)}deg`);
    s.setProperty("--ry", `${((fx - 0.5) * 2 * MAX_TILT).toFixed(2)}deg`);
    s.setProperty("--gx", fx.toFixed(3));
    s.setProperty("--gy", fy.toFixed(3));
  }

  function onPointerMove(e: PointerEvent<HTMLDivElement>) {
    if (e.pointerType === "touch") return;
    const card = (e.target as Element).closest<HTMLElement>("[data-slug]");
    if (card !== hovered.current) {
      reset(hovered.current);
      hovered.current = card;
    }
    if (!card) return;
    pending.current = { x: e.clientX, y: e.clientY, card };
    if (!raf.current) raf.current = requestAnimationFrame(flush);
  }

  function onPointerLeave() {
    reset(hovered.current);
    hovered.current = null;
    pending.current = null;
  }

  function onClick(e: MouseEvent<HTMLDivElement>) {
    const btn = (e.target as Element).closest<HTMLElement>("[data-vote]");
    const card = btn?.closest<HTMLElement>("[data-slug]");
    if (!btn || !card) return;
    const slug = card.dataset.slug ?? "";
    const delta = Number(btn.dataset.vote) > 0 ? 1 : -1;
    vote(slug, delta);
    restartClass(card.querySelector("[data-score]"), "spm-pop");
    const fx = card.querySelector(".spm-fx");
    if (delta > 0) {
      fx?.classList.remove("spm-shake");
      restartClass(fx, "spm-wobble");
      const r = btn.getBoundingClientRect();
      const origin = {
        x: (r.left + r.width / 2) / window.innerWidth,
        y: (r.top + r.height / 2) / window.innerHeight,
      };
      void import("canvas-confetti").then(({ default: confetti }) =>
        confetti({ particleCount: 90, spread: 75, startVelocity: 38, origin, colors: NEON, scalar: 1.1 }),
      );
    } else {
      fx?.classList.remove("spm-wobble");
      restartClass(fx, "spm-shake");
    }
  }

  return (
    <div
      id={id}
      ref={ref}
      className="spm-grid"
      onPointerMove={onPointerMove}
      onPointerLeave={onPointerLeave}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
