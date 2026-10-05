import { describe, expect, it } from "vitest";
import { TEMPLATES, generateShitpost, getTemplate, seededRandom } from "./generator";

describe("seededRandom", () => {
  it("is deterministic and in [0, 1)", () => {
    const a = seededRandom(42);
    const b = seededRandom(42);
    for (let i = 0; i < 100; i++) {
      const x = a();
      expect(x).toBe(b());
      expect(x).toBeGreaterThanOrEqual(0);
      expect(x).toBeLessThan(1);
    }
  });

  it("differs across seeds", () => {
    expect(seededRandom(1)()).not.toBe(seededRandom(2)());
  });
});

describe("generateShitpost", () => {
  it("is deterministic for the same seed", () => {
    expect(generateShitpost(1337)).toEqual(generateShitpost(1337));
  });

  it("returns non-empty text and a known template", () => {
    const ids = new Set(TEMPLATES.map((t) => t.id));
    for (let seed = 0; seed < 200; seed++) {
      const p = generateShitpost(seed);
      expect(p.top.length).toBeGreaterThan(0);
      expect(p.bottom.length).toBeGreaterThan(0);
      expect(ids.has(p.template)).toBe(true);
    }
  });

  it("produces variety", () => {
    const tops = new Set(Array.from({ length: 50 }, (_, i) => generateShitpost(i).top));
    expect(tops.size).toBeGreaterThan(10);
  });
});

describe("getTemplate", () => {
  it("falls back to the first template", () => {
    expect(getTemplate("nope")).toBe(TEMPLATES[0]);
  });
});
