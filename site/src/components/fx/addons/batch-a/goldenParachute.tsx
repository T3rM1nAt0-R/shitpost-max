"use client";

import { useEffect } from "react";
import type { Addon } from "../types";
import { chaChingA, reducedMotion, slideWhistle, spawn } from "./util";

const DURATION = 7600;
let active = false;
let firedThisView = false;

function drop() {
  if (active) return;
  active = true;
  window.setTimeout(() => {
    active = false;
  }, DURATION);
  slideWhistle();
  window.setTimeout(chaChingA, 3000);

  const outer = document.createElement("div");
  outer.className = reducedMotion() ? "fxa-chute fxa-chute-still" : "fxa-chute";
  outer.setAttribute("role", "status");
  const sway = document.createElement("div");
  sway.className = "fxa-chute-sway";
  sway.setAttribute("aria-hidden", "true");
  const chute = document.createElement("span");
  chute.className = "fxa-chute-emoji";
  chute.textContent = "🪂";
  const bag = document.createElement("span");
  bag.className = "fxa-chute-bag";
  bag.textContent = "💰";
  sway.append(chute, bag);
  const caption = document.createElement("p");
  caption.className = "fxa-chute-caption";
  caption.textContent = "You reached the bottom. Here's $40M for your trouble.";
  const fine = document.createElement("span");
  fine.className = "fxa-chute-fine";
  fine.textContent = "Performance-based. Performance not required.";
  caption.appendChild(fine);
  outer.append(sway, caption);
  spawn(outer, DURATION);
}

/** Watches for the user hitting rock bottom, like a CEO right before the bonus. */
function GoldenParachuteWatcher() {
  useEffect(() => {
    const sentinel = document.createElement("div");
    sentinel.setAttribute("aria-hidden", "true");
    sentinel.style.cssText = "width:1px;height:1px;pointer-events:none;";
    document.body.appendChild(sentinel);

    const io = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        // only reward actual scrolling, not short pages that load already at the bottom
        if (firedThisView || window.scrollY < 200) return;
        firedThisView = true;
        io.disconnect();
        drop();
      },
      { rootMargin: "0px 0px 40px 0px" },
    );
    io.observe(sentinel);
    return () => {
      io.disconnect();
      sentinel.remove();
    };
  }, []);
  return null;
}

export const goldenParachuteAddon: Addon = {
  id: "golden-parachute",
  emoji: "🪂",
  label: "Golden Parachute",
  blurb: "Fail upward at terminal velocity. Deploy anytime.",
  run: drop,
  Component: GoldenParachuteWatcher,
};
