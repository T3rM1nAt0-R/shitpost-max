import { useSyncExternalStore } from "react";

/* ---------- persisted value store (localStorage, with in-memory fallback) ---------- */

export interface Persisted {
  get(): string | null;
  set(v: string | null): void;
  subscribe(listener: () => void): () => void;
}

export function persisted(key: string): Persisted {
  const listeners = new Set<() => void>();
  let mem: string | null = null;
  const get = () => {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return mem;
    }
  };
  return {
    get,
    set(v) {
      mem = v;
      try {
        if (v === null) window.localStorage.removeItem(key);
        else window.localStorage.setItem(key, v);
      } catch {
        /* storage blocked: memory fallback only */
      }
      listeners.forEach((l) => l());
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

const serverNull = () => null;

/** Subscribe a component to a persisted value (null on the server / first paint). */
export function usePersisted(store: Persisted): string | null {
  return useSyncExternalStore(store.subscribe, store.get, serverNull);
}

/* ---------- misc ---------- */

export function reducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true
  );
}

export function pick<T>(list: readonly T[]): T {
  return list[Math.floor(Math.random() * list.length)];
}

/* ---------- tiny DOM toast (textContent only, removed when done) ---------- */

export type ToastWhere = "br" | "tr" | "tc";

export interface ToastOptions {
  text: string;
  /** Small heading line above the text. */
  title?: string;
  where?: ToastWhere;
  ms?: number;
  /** Only one toast per slot is ever on screen; a new one replaces the old. */
  slot?: string;
  /** Render as a speech bubble with a tail. */
  bubble?: boolean;
  action?: { label: string; onClick: () => void };
}

const slots = new Map<string, () => void>();

export function toast({
  text,
  title,
  where = "tc",
  ms = 3600,
  slot,
  bubble,
  action,
}: ToastOptions): () => void {
  if (slot) slots.get(slot)?.();

  const el = document.createElement("div");
  el.className = `fxb-toast fxb-${where}${bubble ? " fxb-bubble" : ""}`;
  el.setAttribute("role", "status");
  if (title) {
    const h = document.createElement("strong");
    h.className = "fxb-toast-title";
    h.textContent = title;
    el.appendChild(h);
  }
  const p = document.createElement("span");
  p.textContent = text;
  el.appendChild(p);

  let timer = 0;
  let gone = false;
  const dismiss = () => {
    if (gone) return;
    gone = true;
    window.clearTimeout(timer);
    if (slot && slots.get(slot) === dismiss) slots.delete(slot);
    el.classList.add("fxb-out");
    window.setTimeout(() => el.remove(), 230);
  };

  if (action) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "fxb-toast-btn";
    b.textContent = action.label;
    b.addEventListener("click", () => {
      action.onClick();
      dismiss();
    });
    el.appendChild(b);
  }

  document.body.appendChild(el);
  timer = window.setTimeout(dismiss, ms);
  if (slot) slots.set(slot, dismiss);
  return dismiss;
}

/** Money/emoji confetti burst, loaded on demand. */
export async function burst(
  origin: { x: number; y: number },
  emojis: string[] = ["💵", "💸", "💰"],
  particleCount = 40,
) {
  if (reducedMotion()) return;
  const confetti = (await import("canvas-confetti")).default;
  const shapes = emojis.map((text) => confetti.shapeFromText({ text, scalar: 2 }));
  confetti({
    particleCount,
    spread: 90,
    startVelocity: 38,
    gravity: 0.9,
    scalar: 2,
    ticks: 140,
    shapes,
    origin,
    disableForReducedMotion: true,
  });
}
