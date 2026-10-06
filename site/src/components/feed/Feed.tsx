"use client";

import { LayoutGroup, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { getFleetWithStats } from "@/lib/fleet";
import ServiceCard from "./ServiceCard";
import { useVotes } from "./votes";

type SortMode = "hot" | "valuable" | "chaos";

const TABS: { id: SortMode; label: string }[] = [
  { id: "hot", label: "🔥 Hot" },
  { id: "valuable", label: "💎 Most Valuable" },
  { id: "chaos", label: "🌀 Chaos" },
];

function shuffled(n: number): number[] {
  const order = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return order;
}

export default function Feed() {
  const fleet = getFleetWithStats();
  const [votes, vote] = useVotes();
  const [mode, setMode] = useState<SortMode>("hot");
  const [query, setQuery] = useState("");
  const [chaosOrder, setChaosOrder] = useState<number[] | null>(null);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const withScore = fleet.map((s, idx) => ({ s, idx, score: s.baseScore + (votes[s.slug] ?? 0) }));
    const filtered = q
      ? withScore.filter(
          ({ s }) =>
            s.slug.includes(q) || s.name.toLowerCase().includes(q) || s.tagline.toLowerCase().includes(q),
        )
      : withScore;
    if (mode === "hot") return [...filtered].sort((a, b) => b.score - a.score);
    if (mode === "valuable") return [...filtered].sort((a, b) => b.s.valuation - a.s.valuation);
    if (!chaosOrder) return filtered;
    const pos = new Map(chaosOrder.map((v, i) => [v, i]));
    return [...filtered].sort((a, b) => (pos.get(a.idx) ?? 0) - (pos.get(b.idx) ?? 0));
  }, [fleet, votes, mode, query, chaosOrder]);

  function selectTab(id: SortMode) {
    if (id === "chaos") setChaosOrder(shuffled(fleet.length));
    setMode(id);
  }

  return (
    <section id="feed" className="mx-auto max-w-7xl scroll-mt-8 px-4 pb-24">
      <div className="mb-8 text-center">
        <h2 className="glitch text-4xl font-black uppercase tracking-tight text-white sm:text-6xl" data-text="The Feed">
          The Feed
        </h2>
        <p className="mt-3 text-zinc-400">
          {fleet.length} portfolio companies. Each one a monument to solving nothing at scale. Vote like it matters
          (it does not).
        </p>
      </div>

      <div className="sticky top-2 z-20 mb-8 flex flex-col items-stretch gap-3 rounded-3xl border border-white/10 bg-black/70 p-3 sm:flex-row sm:items-center sm:justify-between">
        <LayoutGroup id="tabs">
          <div className="flex gap-1 rounded-2xl bg-zinc-900 p-1" role="tablist">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={mode === t.id}
                onClick={() => selectTab(t.id)}
                className="relative flex-1 rounded-xl px-4 py-2 text-sm font-bold text-white sm:flex-none"
              >
                {mode === t.id && (
                  <motion.span
                    layoutId="tab-pill"
                    className="absolute inset-0 rounded-xl bg-gradient-to-r from-fuchsia-500 to-cyan-500"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative">{t.label}</span>
              </button>
            ))}
          </div>
        </LayoutGroup>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search my portfolio of nonsense…"
          aria-label="Search services"
          className="w-full rounded-2xl border border-fuchsia-500/50 bg-zinc-950 px-4 py-2 text-white placeholder:text-zinc-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 sm:w-80"
        />
      </div>

      {visible.length === 0 ? (
        <p className="py-20 text-center text-xl text-zinc-400">
          No results. I&apos;ll just acquire a company called &ldquo;{query}&rdquo;. Done. You&apos;re welcome.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {visible.map(({ s, score }, i) => (
            <ServiceCard key={s.slug} service={s} score={score} rank={i} onVote={vote} />
          ))}
        </div>
      )}
    </section>
  );
}
