"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useVotes } from "./votes";

type SortMode = "hot" | "valuable" | "chaos";

const TABS: { id: SortMode; label: string }[] = [
  { id: "hot", label: "🔥 Hot" },
  { id: "valuable", label: "💎 Most Valuable" },
  { id: "chaos", label: "🌀 Chaos" },
];

interface CardRef {
  el: HTMLElement;
  slug: string;
  idx: number;
  base: number;
  valuation: number;
  search: string;
  rankEl: HTMLElement | null;
  order: number;
  rank: string;
}

function shuffle<T>(arr: T[]): T[] {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function readCards(gridId: string): CardRef[] {
  const grid = document.getElementById(gridId);
  if (!grid) return [];
  return Array.from(grid.querySelectorAll<HTMLElement>("[data-slug]")).map((el, idx) => ({
    el,
    slug: el.dataset.slug ?? "",
    idx,
    base: Number(el.dataset.baseScore) || 0,
    valuation: Number(el.dataset.valuation) || 0,
    search: el.dataset.search ?? "",
    rankEl: el.querySelector<HTMLElement>("[data-rank]"),
    order: -1,
    rank: "",
  }));
}

/**
 * Sort tabs + search. Reorders/filters the server-rendered cards in place (CSS `order` + `hidden`)
 * instead of re-rendering them.
 */
export default function FeedControls({ gridId, emptyId }: { gridId: string; emptyId: string }) {
  const [votes] = useVotes();
  const [mode, setMode] = useState<SortMode>("hot");
  const [query, setQuery] = useState("");
  const [chaos, setChaos] = useState<string[] | null>(null);
  const cards = useRef<CardRef[] | null>(null);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const lastPill = useRef<DOMRect | null>(null);

  useEffect(() => {
    if (!cards.current) cards.current = readCards(gridId);
    const all = cards.current;
    const q = query.trim().toLowerCase();
    const list = q ? all.filter((c) => c.search.includes(q)) : [...all];
    if (mode === "hot") {
      const score = (c: CardRef) => c.base + (votes[c.slug] ?? 0);
      list.sort((a, b) => score(b) - score(a) || a.idx - b.idx);
    } else if (mode === "valuable") {
      list.sort((a, b) => b.valuation - a.valuation || a.idx - b.idx);
    } else if (chaos) {
      const pos = new Map(chaos.map((s, i) => [s, i]));
      list.sort((a, b) => (pos.get(a.slug) ?? 0) - (pos.get(b.slug) ?? 0));
    }
    const shown = new Set<CardRef>();
    list.forEach((c, i) => {
      shown.add(c);
      if (c.order !== i) {
        c.order = i;
        c.el.style.order = String(i);
      }
      const rank = `#${i + 1}`;
      if (c.rank !== rank) {
        c.rank = rank;
        if (c.rankEl) c.rankEl.textContent = rank;
      }
      if (c.el.hidden) c.el.hidden = false;
    });
    for (const c of all) if (!shown.has(c) && !c.el.hidden) c.el.hidden = true;

    const empty = document.getElementById(emptyId);
    if (empty) {
      empty.hidden = list.length > 0;
      const qEl = empty.querySelector("[data-query]");
      if (qEl) qEl.textContent = query;
    }
  }, [gridId, emptyId, votes, mode, query, chaos]);

  // FLIP the gradient pill from the previous tab to the active one (transform only).
  useLayoutEffect(() => {
    const idx = TABS.findIndex((t) => t.id === mode);
    const pill = tabRefs.current[idx]?.querySelector<HTMLElement>(".spm-pill");
    if (!pill) return;
    const next = pill.getBoundingClientRect();
    const prev = lastPill.current;
    lastPill.current = next;
    if (!prev || next.width === 0) return;
    pill.classList.remove("spm-pill-go");
    pill.style.transform = `translateX(${prev.left - next.left}px) scaleX(${prev.width / next.width})`;
    const id = requestAnimationFrame(() => {
      pill.classList.add("spm-pill-go");
      pill.style.transform = "";
    });
    return () => cancelAnimationFrame(id);
  }, [mode]);

  function selectTab(id: SortMode) {
    // Re-measure the current pill in case the layout changed since the last switch.
    const cur = tabRefs.current[TABS.findIndex((t) => t.id === mode)]?.querySelector(".spm-pill");
    if (cur) lastPill.current = cur.getBoundingClientRect();
    if (id === "chaos") setChaos(shuffle((cards.current ?? readCards(gridId)).map((c) => c.slug)));
    setMode(id);
  }

  return (
    <div className="sticky top-2 z-20 mb-8 flex flex-col items-stretch gap-3 rounded-3xl border border-white/10 bg-black/70 p-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-1 rounded-2xl bg-zinc-900 p-1" role="tablist">
        {TABS.map((t, i) => (
          <button
            key={t.id}
            ref={(el) => {
              tabRefs.current[i] = el;
            }}
            type="button"
            role="tab"
            aria-selected={mode === t.id}
            onClick={() => selectTab(t.id)}
            className="relative flex-1 rounded-xl px-4 py-2 text-sm font-bold text-white sm:flex-none"
          >
            <span aria-hidden className="spm-pill" />
            <span className="relative">{t.label}</span>
          </button>
        ))}
      </div>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search my portfolio of nonsense…"
        aria-label="Search services"
        className="w-full rounded-2xl border border-fuchsia-500/50 bg-zinc-950 px-4 py-2 text-white placeholder:text-zinc-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 sm:w-80"
      />
    </div>
  );
}
