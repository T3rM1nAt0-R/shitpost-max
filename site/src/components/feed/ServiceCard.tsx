"use client";

import confetti from "canvas-confetti";
import { motion, useAnimationControls, useMotionValue, useSpring, useTransform } from "framer-motion";
import type { MouseEvent } from "react";
import { formatValuation, type FleetServiceStats } from "@/lib/fleet";

interface Props {
  service: FleetServiceStats;
  score: number;
  rank: number;
  onVote: (slug: string, delta: number) => void;
}

const NEON = ["#ff00e5", "#00d4ff", "#ffe600", "#00ff94", "#ff7a00", "#7a5cff"];

export default function ServiceCard({ service, score, rank, onVote }: Props) {
  const mx = useMotionValue(0.5);
  const my = useMotionValue(0.5);
  const rotateX = useSpring(useTransform(my, [0, 1], [18, -18]), { stiffness: 220, damping: 14 });
  const rotateY = useSpring(useTransform(mx, [0, 1], [-18, 18]), { stiffness: 220, damping: 14 });
  const glareX = useTransform(mx, (v) => `${v * 100}%`);
  const glareY = useTransform(my, (v) => `${v * 100}%`);
  const glare = useTransform(
    [glareX, glareY],
    ([x, y]) => `radial-gradient(circle at ${x} ${y}, rgba(255,255,255,0.25), transparent 55%)`,
  );
  const wobble = useAnimationControls();
  const accent = NEON[rank % NEON.length];

  function onMove(e: MouseEvent<HTMLDivElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    mx.set((e.clientX - r.left) / r.width);
    my.set((e.clientY - r.top) / r.height);
  }
  function onLeave() {
    mx.set(0.5);
    my.set(0.5);
  }

  function upvote(e: MouseEvent<HTMLButtonElement>) {
    onVote(service.slug, 1);
    const r = e.currentTarget.getBoundingClientRect();
    void confetti({
      particleCount: 90,
      spread: 75,
      startVelocity: 38,
      origin: { x: (r.left + r.width / 2) / window.innerWidth, y: (r.top + r.height / 2) / window.innerHeight },
      colors: NEON,
      scalar: 1.1,
    });
    void wobble.start({
      rotate: [0, -6, 6, -4, 4, 0],
      scale: [1, 1.06, 0.97, 1.03, 1],
      transition: { duration: 0.6 },
    });
  }

  function downvote() {
    onVote(service.slug, -1);
    void wobble.start({ x: [0, -12, 12, -8, 8, 0], transition: { duration: 0.45 } });
  }

  return (
    <motion.article
      initial={{ opacity: 0, scale: 0.8, y: 30 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.6, rotate: 20 }}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
      style={{ perspective: 900 }}
    >
      <motion.div animate={wobble}>
        <motion.div
          onMouseMove={onMove}
          onMouseLeave={onLeave}
          whileHover={{ scale: 1.04, rotate: [0, -1.5, 1.5, -1, 0], transition: { rotate: { duration: 0.5 } } }}
          style={{
            rotateX,
            rotateY,
            transformStyle: "preserve-3d",
            borderColor: accent,
            boxShadow: `0 0 22px ${accent}55, inset 0 0 30px ${accent}22`,
          }}
          className="group relative flex h-full flex-col overflow-hidden rounded-3xl border-2 bg-gradient-to-br from-zinc-900 via-zinc-950 to-black p-5"
        >
          <motion.div aria-hidden className="pointer-events-none absolute inset-0" style={{ background: glare }} />
          <div className="flex items-start justify-between gap-3" style={{ transform: "translateZ(40px)" }}>
            <motion.span
              className="text-5xl"
              whileHover={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 0.6 }}
            >
              {service.emoji}
            </motion.span>
            <span className="rounded-full bg-white/10 px-2 py-0.5 font-mono text-xs text-zinc-300">
              #{rank + 1} · {service.ticker}
            </span>
          </div>
          <h3 className="mt-3 text-xl font-black leading-tight text-white" style={{ transform: "translateZ(30px)" }}>
            <a href={service.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
              {service.name}
            </a>
          </h3>
          <p className="mt-2 flex-1 text-sm text-zinc-300">{service.tagline}</p>
          <dl className="mt-4 grid grid-cols-2 gap-2 font-mono text-xs">
            <div className="rounded-xl bg-black/50 p-2">
              <dt className="text-zinc-500">Valuation</dt>
              <dd className="font-bold text-emerald-300">{formatValuation(service.valuation)}</dd>
            </div>
            <div className="rounded-xl bg-black/50 p-2">
              <dt className="text-zinc-500">Engineers replaced</dt>
              <dd className="font-bold text-fuchsia-300">{service.engineersReplaced.toLocaleString("en-US")}</dd>
            </div>
          </dl>
          <div className="mt-4 flex items-center justify-between" style={{ transform: "translateZ(50px)" }}>
            <div className="flex items-center gap-2">
              <motion.button
                type="button"
                aria-label={`Upvote ${service.name}`}
                onClick={upvote}
                whileHover={{ scale: 1.2, rotate: -10 }}
                whileTap={{ scale: 0.7 }}
                className="rounded-xl bg-emerald-500/20 px-3 py-1.5 text-lg font-black text-emerald-300 ring-1 ring-emerald-400/60 hover:bg-emerald-500/40"
              >
                ▲
              </motion.button>
              <motion.span
                key={score}
                initial={{ scale: 1.8, color: "#ffe600" }}
                animate={{ scale: 1, color: "#ffffff" }}
                className="min-w-[4ch] text-center font-mono text-lg font-black"
              >
                {score.toLocaleString("en-US")}
              </motion.span>
              <motion.button
                type="button"
                aria-label={`Downvote ${service.name}`}
                onClick={downvote}
                whileHover={{ scale: 1.2, rotate: 10 }}
                whileTap={{ scale: 0.7 }}
                className="rounded-xl bg-rose-500/20 px-3 py-1.5 text-lg font-black text-rose-300 ring-1 ring-rose-400/60 hover:bg-rose-500/40"
              >
                ▼
              </motion.button>
            </div>
            <a
              href={service.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs uppercase text-cyan-300 hover:text-cyan-100"
            >
              source ↗
            </a>
          </div>
        </motion.div>
      </motion.div>
    </motion.article>
  );
}
