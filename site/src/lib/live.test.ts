import { describe, expect, it } from "vitest";
import { parseLive, timeAgo } from "./live";

describe("parseLive", () => {
  it("keeps well-formed entries and drops the rest", () => {
    const parsed = parseLive({
      services: {
        a: { m: "pi: digit 5 = 9", t: "2026-10-07T00:50:10+05:30" },
        b: { m: 3, t: "2026-10-07T00:50:10+05:30" },
        c: { m: "bad time", t: "not a date" },
        d: null,
      },
    });
    expect(Object.keys(parsed)).toEqual(["a"]);
  });

  it("returns nothing for garbage", () => {
    expect(parseLive(null)).toEqual({});
    expect(parseLive({ services: "x" })).toEqual({});
    expect(parseLive("x")).toEqual({});
  });

  it("caps long messages", () => {
    const parsed = parseLive({ services: { a: { m: "x".repeat(500), t: "2026-10-07T00:00:00Z" } } });
    expect(parsed.a.m.length).toBe(120);
  });
});

describe("timeAgo", () => {
  const now = Date.parse("2026-10-07T12:00:00Z");
  it("formats ages", () => {
    expect(timeAgo("2026-10-07T11:59:40Z", now)).toBe("just now");
    expect(timeAgo("2026-10-07T11:57:00Z", now)).toBe("3m ago");
    expect(timeAgo("2026-10-07T10:00:00Z", now)).toBe("2h ago");
    expect(timeAgo("2026-10-03T12:00:00Z", now)).toBe("4d ago");
  });
  it("never goes negative", () => {
    expect(timeAgo("2026-10-07T12:05:00Z", now)).toBe("just now");
  });
});
