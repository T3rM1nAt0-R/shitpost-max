"use client";

import { useCallback, useSyncExternalStore } from "react";

export const VOTES_KEY = "spm-votes";

export type Votes = Record<string, number>;

/*
 * Shared vote store.
 *
 * - `server`: totals from GET /api/votes (null until/unless the API answers,
 *   e.g. in `next dev` or offline it stays null).
 * - `pending`: optimistic deltas for POSTs still in flight.
 * - localStorage (VOTES_KEY): this browser's own cumulative votes, kept for
 *   continuity and used as the whole picture when the API is unreachable.
 *
 * Snapshot = server totals + pending when the API is available, otherwise the
 * local record. Callers add it to each service's seeded base score.
 */

const EMPTY: Votes = {};
const REFETCH_MIN_MS = 30_000;
const listeners = new Set<() => void>();

let server: Votes | null = null;
let pending: Votes = {};
/** Totals returned by POSTs since the current GET started; they win over that GET's (older) answer. */
let freshTotals: Votes = {};
let fetching = false;
let lastFetchAt = 0;
let started = false;

let lastRaw: string | null = null;
let lastLocal: Votes = EMPTY;
let snapKey: string | null = null;
let snapshot: Votes = EMPTY;

function sanitize(parsed: unknown): Votes {
  const out: Votes = {};
  if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      if (typeof v === "number" && Number.isFinite(v)) out[k] = v;
    }
  }
  return out;
}

function readLocal(): Votes {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(VOTES_KEY);
  } catch {
    return lastLocal;
  }
  if (raw === lastRaw) return lastLocal;
  lastRaw = raw;
  try {
    lastLocal = sanitize(raw ? JSON.parse(raw) : {});
  } catch {
    lastLocal = EMPTY;
  }
  return lastLocal;
}

function writeLocal(next: Votes) {
  const raw = JSON.stringify(next);
  try {
    window.localStorage.setItem(VOTES_KEY, raw);
    lastRaw = raw;
  } catch {
    lastRaw = null;
  }
  lastLocal = next;
}

function emit() {
  listeners.forEach((l) => l());
}

let serverVersion = 0;

function getSnapshot(): Votes {
  const local = readLocal();
  if (server === null) return local;
  const key = `${serverVersion}`;
  if (key === snapKey) return snapshot;
  const out: Votes = { ...server };
  for (const [k, v] of Object.entries(pending)) out[k] = (out[k] ?? 0) + v;
  snapKey = key;
  snapshot = out;
  return out;
}

/** Bump whenever `server` or `pending` changes so the memoised snapshot is rebuilt. */
function changed() {
  serverVersion += 1;
  emit();
}

async function fetchVotes() {
  if (fetching) return;
  fetching = true;
  lastFetchAt = Date.now();
  freshTotals = {};
  try {
    const res = await fetch("/api/votes", { cache: "no-store", headers: { Accept: "application/json" } });
    if (!res.ok || !(res.headers.get("content-type") ?? "").includes("application/json")) return;
    const next = sanitize(await res.json());
    server = { ...next, ...freshTotals };
    changed();
  } catch {
    // API unreachable (next dev, offline): stay local-only.
  } finally {
    fetching = false;
  }
}

function onFocus() {
  if (Date.now() - lastFetchAt >= REFETCH_MIN_MS) void fetchVotes();
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  const onStorage = (e: StorageEvent) => {
    if (e.key === VOTES_KEY) cb();
  };
  window.addEventListener("storage", onStorage);
  if (!started) {
    started = true;
    window.addEventListener("focus", onFocus);
    void fetchVotes();
  }
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", onStorage);
  };
}

function addPending(slug: string, delta: number) {
  const next = (pending[slug] ?? 0) + delta;
  pending = { ...pending };
  if (next === 0) delete pending[slug];
  else pending[slug] = next;
}

async function postVote(slug: string, delta: 1 | -1) {
  addPending(slug, delta);
  changed();
  try {
    const res = await fetch("/api/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug, delta }),
    });
    const data: unknown = res.ok ? await res.json() : null;
    const total = (data as { total?: unknown } | null)?.total;
    if (typeof total === "number" && Number.isFinite(total)) {
      if (server !== null) server = { ...server, [slug]: total };
      freshTotals[slug] = total;
    }
  } catch {
    // Network error: the optimistic delta is dropped below; the local record still has it.
  } finally {
    addPending(slug, -delta);
    changed();
  }
}

/** Vote deltas per slug: shared totals from /api/votes when available, else this browser's own votes. */
export function useVotes(): [Votes, (slug: string, delta: number) => void] {
  const votes = useSyncExternalStore(subscribe, getSnapshot, () => EMPTY);
  const vote = useCallback((slug: string, delta: number) => {
    if (!Number.isFinite(delta) || delta === 0) return;
    const current = readLocal();
    writeLocal({ ...current, [slug]: (current[slug] ?? 0) + delta });
    if (delta === 1 || delta === -1) void postVote(slug, delta);
    else changed();
  }, []);
  return [votes, vote];
}
