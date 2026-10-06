"use client";

import { useEffect, useRef, useSyncExternalStore } from "react";
import type { Addon } from "../types";
import { chaChingA, toast } from "./util";

const KEY = "spm-networth-hud";

/* ---------- tiny external store for the on/off toggle (persisted) ---------- */
const listeners = new Set<() => void>();
let shown: boolean | null = null;

function readShown(): boolean {
  if (shown === null) {
    try {
      shown = window.localStorage.getItem(KEY) === "1"; // default: off (opt in to wealth)
    } catch {
      shown = false;
    }
  }
  return shown;
}
function subscribe(fn: () => void) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
function toggle() {
  shown = !readShown();
  try {
    window.localStorage.setItem(KEY, shown ? "1" : "0");
  } catch {
    /* private mode: stay rich in-memory only */
  }
  listeners.forEach((fn) => fn());
  if (shown) chaChingA();
  toast(
    shown
      ? "Net worth tracker on. Please read slower, we're compounding."
      : "Net worth hidden. Like a real billionaire: offshore.",
  );
}

/* ---------- the absurd accelerating money curve ---------- */
/** Dollars earned after `s` seconds of reading. Starts at a cent/sec, ends at "GDP of France". */
function worth(s: number) {
  return 0.01 * s + 3 * s ** 2 + 0.6 * s ** 3 + 2 * Math.exp(s / 9);
}

const UNITS: Array<[number, string]> = [
  [1e15, "quadrillion"],
  [1e12, "trillion"],
  [1e9, "billion"],
  [1e6, "million"],
];
function fmt(n: number) {
  if (!Number.isFinite(n)) return "$∞ (we broke math, stock up 4%)";
  if (n >= 1e18) return `$${(n / 1e18).toFixed(2)} quintillion`;
  for (const [v, name] of UNITS) if (n >= v) return `$${(n / v).toFixed(2)} ${name}`;
  return `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const QUIPS: Array<[number, string]> = [
  [0, "mostly unrealized"],
  [100, "that's a sandwich, peasant"],
  [10_000, "pocket lint tier"],
  [1e6, "first yacht (small, embarrassing)"],
  [1e8, "bought the yacht a yacht"],
  [1e9, "officially a billionaire. taxes: optional"],
  [1e11, "rocket to nowhere: funded"],
  [1e13, "purchased the moon. returning it"],
  [1e16, "money is now a vibe, not a number"],
];
function quip(n: number) {
  let q = QUIPS[0][1];
  for (const [v, text] of QUIPS) if (n >= v) q = text;
  return q;
}

function NetWorthHud() {
  const visible = useSyncExternalStore(subscribe, readShown, () => false);
  const amountRef = useRef<HTMLSpanElement>(null);
  const quipRef = useRef<HTMLSpanElement>(null);
  const elapsed = useRef(0); // seconds of visible reading time, survives hide/show

  useEffect(() => {
    if (!visible) return;
    let timer: number | undefined;
    let last = 0;
    const tick = () => {
      const now = performance.now();
      elapsed.current += (now - last) / 1000;
      last = now;
      const n = worth(elapsed.current);
      if (amountRef.current) amountRef.current.textContent = fmt(n);
      if (quipRef.current) quipRef.current.textContent = quip(n);
    };
    const start = () => {
      if (timer !== undefined || document.hidden) return;
      last = performance.now();
      tick();
      timer = window.setInterval(tick, 100); // max 10 updates/sec
    };
    const stop = () => {
      if (timer === undefined) return;
      window.clearInterval(timer);
      timer = undefined;
    };
    const onVis = () => (document.hidden ? stop() : start());
    document.addEventListener("visibilitychange", onVis);
    start();
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [visible]);

  if (!visible) return null;
  return (
    <div className="fxa-hud" role="timer" aria-live="off">
      <span className="fxa-hud-label">Your net worth while reading:</span>{" "}
      <span ref={amountRef} className="fxa-hud-amount">
        $0.00
      </span>
      <span ref={quipRef} className="fxa-hud-quip">
        mostly unrealized
      </span>
    </div>
  );
}

export const netWorthHudAddon: Addon = {
  id: "net-worth-hud",
  emoji: "📈",
  label: "Net Worth HUD",
  blurb: "Get paid to read. Exponentially. It's called passive income, look it up.",
  run: toggle,
  Component: NetWorthHud,
};
