"use client";

import { useEffect, useRef } from "react";
import { formatValuation } from "@/lib/fleet";

interface Props {
  to: number;
  money?: boolean;
  prefix?: string;
  suffix?: string;
}

function fmt(v: number, { money, prefix = "", suffix = "" }: Omit<Props, "to">): string {
  return money ? formatValuation(v) : `${prefix}${Math.round(v).toLocaleString("en-US")}${suffix}`;
}

/** Counts 0 → `to` once when scrolled into view. Server HTML already holds the final value. */
export default function CountUp({ to, money, prefix, suffix }: Props) {
  const ref = useRef<HTMLSpanElement>(null);
  const opts = { money, prefix, suffix };
  const final = fmt(to, opts);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const o = { money, prefix, suffix };
    let raf = 0;
    const io = new IntersectionObserver((entries) => {
      if (!entries.some((e) => e.isIntersecting)) return;
      io.disconnect();
      const start = performance.now();
      const step = (now: number) => {
        const t = Math.min(1, (now - start) / 2400);
        const eased = 1 - Math.pow(1 - t, 4);
        el.textContent = t < 1 ? fmt(to * eased, o) : fmt(to, o);
        if (t < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
    });
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [to, money, prefix, suffix]);

  return (
    <span ref={ref} data-money>
      {final}
    </span>
  );
}
