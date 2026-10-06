"use client";

import { useEffect } from "react";
import { LIVE_URL, parseLive, timeAgo, type LiveServices } from "@/lib/live";

const REFETCH_MS = 5 * 60_000;
const REPAINT_MS = 30_000;

/**
 * Fills each card's `[data-live]` line with that service's latest commit, straight from the repo.
 * Renders nothing; like FeedGrid it writes text into the static cards directly (textContent only,
 * so nothing from the network is ever treated as HTML). If the fetch fails the lines just stay hidden.
 */
export default function LiveFeed({ gridId }: { gridId: string }) {
  useEffect(() => {
    const grid = document.getElementById(gridId);
    if (!grid) return;

    let live: LiveServices = {};
    let stopped = false;

    const paint = () => {
      const now = Date.now();
      grid.querySelectorAll<HTMLElement>("[data-slug]").forEach((card) => {
        const line = card.querySelector<HTMLElement>("[data-live]");
        const entry = live[card.dataset.slug ?? ""];
        if (!line || !entry) return;
        line.textContent = `▸ ${entry.m} · ${timeAgo(entry.t, now)}`;
        line.hidden = false;
      });
    };

    const load = async () => {
      if (document.hidden) return;
      try {
        const res = await fetch(LIVE_URL, { headers: { Accept: "application/json" } });
        if (!res.ok) return;
        const parsed = parseLive(await res.json());
        if (stopped || Object.keys(parsed).length === 0) return;
        live = parsed;
        paint();
      } catch {
        /* offline or blocked: leave the lines hidden */
      }
    };

    load();
    const refetch = window.setInterval(load, REFETCH_MS);
    const repaint = window.setInterval(() => {
      if (!document.hidden) paint();
    }, REPAINT_MS);
    const onVisible = () => {
      if (!document.hidden) load();
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      stopped = true;
      window.clearInterval(refetch);
      window.clearInterval(repaint);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [gridId]);

  return null;
}
