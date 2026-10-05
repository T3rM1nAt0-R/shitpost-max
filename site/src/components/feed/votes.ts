"use client";

import { useCallback, useSyncExternalStore } from "react";

export const VOTES_KEY = "spm-votes";

export type Votes = Record<string, number>;

const EMPTY: Votes = {};
const listeners = new Set<() => void>();
let lastRaw: string | null = null;
let lastParsed: Votes = EMPTY;

function readVotes(): Votes {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(VOTES_KEY);
  } catch {
    return lastParsed;
  }
  if (raw === lastRaw) return lastParsed;
  lastRaw = raw;
  try {
    const parsed: unknown = raw ? JSON.parse(raw) : {};
    const out: Votes = {};
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
        if (typeof v === "number" && Number.isFinite(v)) out[k] = v;
      }
    }
    lastParsed = out;
  } catch {
    lastParsed = EMPTY;
  }
  return lastParsed;
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  const onStorage = (e: StorageEvent) => {
    if (e.key === VOTES_KEY) cb();
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", onStorage);
  };
}

function writeVotes(next: Votes) {
  const raw = JSON.stringify(next);
  try {
    window.localStorage.setItem(VOTES_KEY, raw);
    lastRaw = raw;
  } catch {
    lastRaw = null;
  }
  lastParsed = next;
  listeners.forEach((l) => l());
}

/** Vote deltas per slug, persisted in localStorage under "spm-votes". */
export function useVotes(): [Votes, (slug: string, delta: number) => void] {
  const votes = useSyncExternalStore(subscribe, readVotes, () => EMPTY);
  const vote = useCallback((slug: string, delta: number) => {
    const current = readVotes();
    writeVotes({ ...current, [slug]: (current[slug] ?? 0) + delta });
  }, []);
  return [votes, vote];
}
