import { describe, expect, it } from "vitest";
import {
  SLUG_RE,
  applyVote,
  clientIp,
  createRateLimiter,
  parseFleet,
  parseVoteBody,
  parseVotesFile,
  validateVote,
} from "../../api/lib.mjs";
import fleet from "./fleet.json";

const allow = new Set(["cert-watch", "aqi-blr"]);

describe("votes API: validation", () => {
  it("accepts a valid vote", () => {
    expect(validateVote({ slug: "cert-watch", delta: 1 }, allow)).toEqual({ ok: true, slug: "cert-watch", delta: 1 });
    expect(validateVote({ slug: "aqi-blr", delta: -1 }, allow)).toEqual({ ok: true, slug: "aqi-blr", delta: -1 });
  });

  it("rejects bad slugs, unknown slugs and bad deltas", () => {
    expect(validateVote({ slug: "Cert-Watch", delta: 1 }, allow)).toMatchObject({ ok: false, error: "bad slug" });
    expect(validateVote({ slug: "a".repeat(65), delta: 1 }, allow)).toMatchObject({ ok: false });
    expect(validateVote({ slug: "../etc", delta: 1 }, allow)).toMatchObject({ ok: false, error: "bad slug" });
    expect(validateVote({ slug: "nope", delta: 1 }, allow)).toMatchObject({ ok: false, error: "unknown slug" });
    for (const delta of [0, 2, -2, "1", 1.5, null]) {
      expect(validateVote({ slug: "cert-watch", delta }, allow)).toMatchObject({ ok: false, error: "bad delta" });
    }
    expect(validateVote(null, allow)).toMatchObject({ ok: false });
    expect(validateVote([], allow)).toMatchObject({ ok: false });
  });

  it("parses raw bodies", () => {
    expect(parseVoteBody('{"slug":"cert-watch","delta":1}', allow)).toMatchObject({ ok: true });
    expect(parseVoteBody("{nope", allow)).toEqual({ ok: false, error: "bad json" });
    expect(parseVoteBody('{"slug":"__proto__","delta":1}', allow)).toMatchObject({ ok: false });
  });

  it("every real fleet slug matches the slug pattern", () => {
    for (const s of fleet as string[]) expect(SLUG_RE.test(s)).toBe(true);
  });
});

describe("votes API: files", () => {
  it("parses the fleet allowlist", () => {
    expect([...parseFleet('["a-b","BAD",3,"c"]')]).toEqual(["a-b", "c"]);
    expect(() => parseFleet('{"a":1}')).toThrow();
  });

  it("parses persisted totals and rejects corrupt files", () => {
    expect({ ...parseVotesFile('{"a":3,"b":-2,"c":"x","D":1,"e":1.5}') }).toEqual({ a: 3, b: -2 });
    expect(() => parseVotesFile("{trunc")).toThrow();
    expect(() => parseVotesFile("[1,2]")).toThrow();
  });
});

describe("votes API: applyVote", () => {
  it("accumulates totals", () => {
    const totals: Record<string, number> = {};
    expect(applyVote(totals, "a", 1)).toBe(1);
    expect(applyVote(totals, "a", 1)).toBe(2);
    expect(applyVote(totals, "a", -1)).toBe(1);
    expect(applyVote(totals, "b", -1)).toBe(-1);
    expect(totals).toEqual({ a: 1, b: -1 });
  });
});

describe("votes API: rate limiter", () => {
  it("allows a burst up to capacity, then refuses, then refills", () => {
    const rl = createRateLimiter({ capacity: 30, windowMs: 60_000 });
    const t0 = 1_000_000;
    for (let i = 0; i < 30; i++) expect(rl.take("1.2.3.4", t0)).toBe(true);
    expect(rl.take("1.2.3.4", t0)).toBe(false);
    expect(rl.take("5.6.7.8", t0)).toBe(true); // independent per key
    expect(rl.take("1.2.3.4", t0 + 1_000)).toBe(false); // 0.5 token after 1s
    expect(rl.take("1.2.3.4", t0 + 2_000)).toBe(true); // 1 token after 2s
    expect(rl.take("1.2.3.4", t0 + 2_000)).toBe(false);
  });

  it("prunes fully refilled buckets and caps key count", () => {
    const rl = createRateLimiter({ capacity: 2, windowMs: 1_000, maxKeys: 3 });
    rl.take("a", 0);
    rl.take("b", 0);
    rl.prune(5_000);
    expect(rl.size).toBe(0);
    for (const k of ["a", "b", "c", "d", "e"]) rl.take(k, 0);
    expect(rl.size).toBeLessThanOrEqual(3);
  });
});

describe("votes API: clientIp", () => {
  it("prefers CF-Connecting-IP, falls back to the socket", () => {
    expect(clientIp({ "cf-connecting-ip": "203.0.113.9" }, "172.18.0.2")).toBe("203.0.113.9");
    expect(clientIp({}, "172.18.0.2")).toBe("172.18.0.2");
    expect(clientIp({}, undefined)).toBe("unknown");
  });
});
