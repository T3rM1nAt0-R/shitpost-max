"use client";

import { animate, motion, useInView, useMotionValue, useTransform } from "framer-motion";
import { useEffect, useRef } from "react";
import { formatValuation, getFleetWithStats, totalEngineersReplaced, totalValuation } from "@/lib/fleet";

type Stat =
  | { label: string; kind: "count"; to: number; suffix?: string; prefix?: string }
  | { label: string; kind: "money"; to: number }
  | { label: string; kind: "static"; value: string };

function CountUp({ stat }: { stat: Exclude<Stat, { kind: "static" }> }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const mv = useMotionValue(0);
  const text = useTransform(mv, (v) =>
    stat.kind === "money"
      ? formatValuation(v)
      : `${stat.prefix ?? ""}${Math.round(v).toLocaleString("en-US")}${stat.suffix ?? ""}`,
  );

  useEffect(() => {
    if (!inView) return;
    const controls = animate(mv, stat.to, { duration: 2.4, ease: [0.16, 1, 0.3, 1] });
    return () => controls.stop();
  }, [inView, mv, stat.to]);

  return <motion.span ref={ref}>{text}</motion.span>;
}

export default function Stats() {
  const stats: Stat[] = [
    { label: "Microservices (one-person, zero people)", kind: "count", to: getFleetWithStats().length },
    { label: "Fleet valuation (audited by vibes)", kind: "money", to: totalValuation() },
    { label: "Engineers replaced (lower bound)", kind: "count", to: totalEngineersReplaced() },
    { label: "Engineer multiplier", kind: "count", to: 1_000_000, suffix: "x" },
    { label: "Problems solved that existed", kind: "static", value: "0" },
    { label: "Yachts per microservice", kind: "static", value: "∞" },
  ];

  return (
    <section className="mx-auto grid max-w-7xl grid-cols-2 gap-4 px-4 py-12 md:grid-cols-3 lg:grid-cols-6">
      {stats.map((s, idx) => (
        <motion.div
          key={s.label}
          initial={{ opacity: 0, y: 40, rotate: idx % 2 ? 6 : -6 }}
          whileInView={{ opacity: 1, y: 0, rotate: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 160, damping: 12, delay: idx * 0.08 }}
          whileHover={{ scale: 1.06, rotate: idx % 2 ? -2 : 2 }}
          className="rounded-2xl border border-white/10 bg-gradient-to-br from-zinc-900 to-black p-4 text-center shadow-[0_0_24px_rgba(34,211,238,0.25)]"
        >
          <div className="break-words bg-gradient-to-r from-cyan-300 via-fuchsia-400 to-yellow-300 bg-clip-text font-mono text-xl font-black text-transparent sm:text-2xl">
            {s.kind === "static" ? s.value : <CountUp stat={s} />}
          </div>
          <div className="mt-2 text-xs uppercase tracking-wider text-zinc-400">{s.label}</div>
        </motion.div>
      ))}
    </section>
  );
}
