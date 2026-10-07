/** Where the fleet publishes each service's latest commit (see harness/live.py in the repo). */
export const LIVE_URL = "https://raw.githubusercontent.com/T3rM1nAt0-R/shitpost-max/main/live/live.json";

export interface LiveEntry {
  /** Latest commit message. */
  m: string;
  /** Commit time, ISO 8601. */
  t: string;
}

export type LiveServices = Record<string, LiveEntry>;

const MAX_MESSAGE_CHARS = 120;

/** Accepts the fetched JSON and keeps only well-formed entries; anything else is dropped. */
export function parseLive(raw: unknown): LiveServices {
  const out: LiveServices = {};
  const services = (raw as { services?: unknown } | null)?.services;
  if (!services || typeof services !== "object") return out;
  for (const [slug, entry] of Object.entries(services as Record<string, unknown>)) {
    const e = entry as Partial<LiveEntry> | null;
    if (!e || typeof e.m !== "string" || typeof e.t !== "string") continue;
    if (Number.isNaN(Date.parse(e.t))) continue;
    out[slug] = { m: e.m.slice(0, MAX_MESSAGE_CHARS), t: e.t };
  }
  return out;
}

/** "just now", "3m ago", "2h ago", "4d ago". */
export function timeAgo(iso: string, now: number = Date.now()): string {
  const seconds = Math.max(0, Math.round((now - Date.parse(iso)) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
