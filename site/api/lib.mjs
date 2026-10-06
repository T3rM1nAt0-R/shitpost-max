// Pure logic for the shitpostmax upvotes API. No I/O, no dependencies.

export const SLUG_RE = /^[a-z0-9-]{1,64}$/;
export const MAX_BODY_BYTES = 1024;

/** Parse fleet.json (a JSON array of slugs) into an allowlist Set. Throws on bad input. */
export function parseFleet(text) {
  const parsed = JSON.parse(text);
  if (!Array.isArray(parsed)) throw new Error("fleet file must be a JSON array");
  return new Set(parsed.filter((s) => typeof s === "string" && SLUG_RE.test(s)));
}

/** Parse a persisted votes file into a plain {slug: integer} object. Throws on corrupt input. */
export function parseVotesFile(text) {
  const parsed = JSON.parse(text);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("votes file must be a JSON object");
  }
  const out = Object.create(null);
  for (const [k, v] of Object.entries(parsed)) {
    if (SLUG_RE.test(k) && Number.isInteger(v)) out[k] = v;
  }
  return out;
}

/**
 * Validate a POST /api/vote body.
 * @returns {{ok: true, slug: string, delta: 1 | -1} | {ok: false, error: string}}
 */
export function validateVote(body, allow) {
  if (!body || typeof body !== "object" || Array.isArray(body)) return { ok: false, error: "bad body" };
  const { slug, delta } = body;
  if (typeof slug !== "string" || !SLUG_RE.test(slug)) return { ok: false, error: "bad slug" };
  if (!allow.has(slug)) return { ok: false, error: "unknown slug" };
  if (delta !== 1 && delta !== -1) return { ok: false, error: "bad delta" };
  return { ok: true, slug, delta };
}

/** Parse and validate a raw request body string. */
export function parseVoteBody(text, allow) {
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    return { ok: false, error: "bad json" };
  }
  return validateVote(body, allow);
}

/** Apply a vote to the totals map (mutates) and return the new total. */
export function applyVote(totals, slug, delta) {
  const next = (totals[slug] ?? 0) + delta;
  totals[slug] = next;
  return next;
}

/** Per-key token bucket: `capacity` tokens, refilled at capacity per `windowMs`. */
export function createRateLimiter({ capacity = 30, windowMs = 60_000, maxKeys = 10_000 } = {}) {
  const rate = capacity / windowMs;
  const buckets = new Map();
  return {
    take(key, now = Date.now()) {
      let b = buckets.get(key);
      if (!b) {
        if (buckets.size >= maxKeys) this.prune(now);
        if (buckets.size >= maxKeys) buckets.delete(buckets.keys().next().value);
        b = { tokens: capacity, at: now };
        buckets.set(key, b);
      } else {
        b.tokens = Math.min(capacity, b.tokens + (now - b.at) * rate);
        b.at = now;
      }
      if (b.tokens < 1) return false;
      b.tokens -= 1;
      return true;
    },
    /** Drop buckets that have fully refilled (they behave the same as absent ones). */
    prune(now = Date.now()) {
      for (const [k, b] of buckets) {
        if (b.tokens + (now - b.at) * rate >= capacity) buckets.delete(k);
      }
    },
    get size() {
      return buckets.size;
    },
  };
}

/** Pick the client IP: Cloudflare's header first, then the socket address. */
export function clientIp(headers, remoteAddress) {
  const cf = headers["cf-connecting-ip"];
  const v = Array.isArray(cf) ? cf[0] : cf;
  if (typeof v === "string" && v.length > 0 && v.length <= 64) return v.trim();
  return remoteAddress || "unknown";
}
