"use client";

import { motion } from "framer-motion";
import { getFleetWithStats } from "@/lib/fleet";

const SPECIALS = [
  { ticker: "$PI", change: "+∞%" },
  { ticker: "$VIBES", change: "+420.69%" },
  { ticker: "$YACHT", change: "+9001%" },
  { ticker: "$PROBLEMS", change: "-100%" },
  { ticker: "$ENGINEERS", change: "-∞%" },
  { ticker: "$MOON", change: "ACQUIRED" },
];

export default function Ticker() {
  const fleet = getFleetWithStats().slice(0, 40);
  const items = [
    ...SPECIALS.map((s) => ({ ...s, up: !s.change.startsWith("-") })),
    ...fleet.map((f) => ({
      ticker: f.ticker,
      change: `${f.change >= 0 ? "+" : ""}${f.change}%`,
      up: f.change >= 0,
    })),
  ];
  const row = [...items, ...items];

  return (
    <div
      className="relative overflow-hidden border-y-2 border-fuchsia-500/70 bg-black py-3 shadow-[0_0_30px_rgba(217,70,239,0.5)]"
      aria-label="Fake stock ticker"
    >
      <motion.div
        className="flex w-max gap-10 whitespace-nowrap font-mono text-sm font-bold sm:text-base"
        animate={{ x: ["0%", "-50%"] }}
        transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
      >
        {row.map((it, idx) => (
          <span key={idx} className="flex items-center gap-2">
            <span className="text-white">{it.ticker}</span>
            <span className={it.up ? "text-emerald-400" : "text-rose-500"}>
              {it.up ? "▲" : "▼"} {it.change}
            </span>
          </span>
        ))}
      </motion.div>
    </div>
  );
}
