"use client";

import { useEffect, useRef } from "react";
import type { Addon } from "../types";
import { ahem } from "./sound";
import { persisted, pick, toast, usePersisted } from "./util";

const hired = persisted("fxb-butler");
const THROTTLE_MS = 1400;
const TALK_MS = 2600;

const ON_BUTTON = [
  "Sir, that button is beneath you.",
  "Shall I have someone press that for you, sir?",
  "Sir has pressed enough buttons today. The staff are exhausted from watching.",
  "I took the liberty of buying that button. And its family.",
  "A gentleman does not click. A gentleman gestures vaguely.",
  "That button was made by poor people, sir. Wash your cursor afterwards.",
  "Shall I alert the press? Sir is about to press.",
] as const;

const ON_LINK = [
  "Sir, that link leads to a place you could simply purchase.",
  "Following links is what interns are for, sir.",
  "Sir, that page is not in the will.",
  "I've pre-read that page, sir. It's full of opinions from people with mortgages.",
  "Shall I fetch the carriage? It's three pixels away.",
  "Sir, you own that URL now. I bought it while you were hovering.",
  "One does not click links, sir. One has links clicked.",
] as const;

/** A tiny butler who judges every link and button you hover. Transform-only motion. */
function Butler() {
  const on = usePersisted(hired) === "1";
  const rootRef = useRef<HTMLDivElement>(null);
  const bubbleRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!on) return;
    let last = 0;
    let lastTarget: Element | null = null;
    let hideTimer = 0;

    const onOver = (e: PointerEvent) => {
      const now = performance.now();
      if (now - last < THROTTLE_MS) return;
      const target = (e.target as Element | null)?.closest?.("a, button, [role='button']");
      const root = rootRef.current;
      const bubble = bubbleRef.current;
      if (!target || !root || !bubble || target === lastTarget) return;
      last = now;
      lastTarget = target;

      bubble.textContent = pick(target.tagName === "A" ? ON_LINK : ON_BUTTON);

      // Shuffle toward the hovered element horizontally (layout read once per throttled hover).
      const t = target.getBoundingClientRect();
      const home = root.offsetLeft + root.offsetWidth / 2;
      const dx = Math.max(-window.innerWidth * 0.4, Math.min(0, t.left + t.width / 2 - home));
      root.style.transform = `translateX(${Math.round(dx)}px)`;
      root.classList.add("fxb-talk");

      window.clearTimeout(hideTimer);
      hideTimer = window.setTimeout(() => {
        root.classList.remove("fxb-talk");
        root.style.transform = "";
        lastTarget = null;
      }, TALK_MS);
    };

    document.addEventListener("pointerover", onOver, { passive: true });
    return () => {
      document.removeEventListener("pointerover", onOver);
      window.clearTimeout(hideTimer);
    };
  }, [on]);

  if (!on) return null;
  return (
    <div ref={rootRef} className="fxb-butler" aria-hidden="true">
      <span ref={bubbleRef} className="fxb-butler-bubble" />
      <span className="fxb-butler-body">🤵</span>
    </div>
  );
}

function toggleButler() {
  ahem();
  const now = hired.get() !== "1";
  hired.set(now ? "1" : null);
  toast({
    title: now ? "🤵 BUTLER HIRED" : "🚪 BUTLER FIRED",
    text: now
      ? "Jeeves has joined. Salary: your dignity, paid quarterly. He will now judge everything you hover."
      : "Butler dismissed. He took the silverware and, somehow, your credit score.",
    ms: 4000,
    slot: "butler",
  });
}

export const butlerAddon: Addon = {
  id: "hire-butler",
  emoji: "🤵",
  label: "Hire a Butler",
  blurb: "A man whose only job is to disapprove of your clicks. Tap again to fire him.",
  run: toggleButler,
  Component: Butler,
};
