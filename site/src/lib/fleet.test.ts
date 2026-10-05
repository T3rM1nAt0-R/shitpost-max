import { describe, expect, it } from "vitest";
import { formatValuation, getFleet } from "./fleet";

describe("getFleet", () => {
  it("is non-empty", () => {
    expect(getFleet().length).toBeGreaterThan(0);
  });

  it("has unique slugs", () => {
    const slugs = getFleet().map((s) => s.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
  });

  it("is deterministic across calls", () => {
    expect(getFleet()).toEqual(getFleet());
  });
});

describe("formatValuation", () => {
  it("returns a string containing $", () => {
    for (const n of [0, 999, 1_000_000, 4.2e12]) {
      const s = formatValuation(n);
      expect(typeof s).toBe("string");
      expect(s).toContain("$");
    }
  });
});
