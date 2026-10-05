"use client";

import confetti from "canvas-confetti";
import { useEffect, useRef, useState } from "react";
import { chaChing, fanfare } from "./sound";

const KONAMI = [
  "ArrowUp",
  "ArrowUp",
  "ArrowDown",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "ArrowLeft",
  "ArrowRight",
  "b",
  "a",
];

let moneyShapes: confetti.Shape[] | null = null;
function shapes(): confetti.Shape[] {
  moneyShapes ??= ["💵", "💸", "💰", "🪙"].map((text) =>
    confetti.shapeFromText({ text, scalar: 2.2 }),
  );
  return moneyShapes;
}

function rain(intensity = 1) {
  const s = shapes();
  const fire = (x: number) =>
    confetti({
      particleCount: Math.round(40 * intensity),
      spread: 100,
      startVelocity: 45,
      gravity: 0.9,
      scalar: 2.2,
      shapes: s,
      origin: { x, y: 0.05 },
      disableForReducedMotion: true,
    });
  fire(0.2);
  fire(0.5);
  fire(0.8);
}

function storm(ms: number) {
  const end = Date.now() + ms;
  const colors = ["#ffd700", "#ff2bd6", "#00f0ff", "#b6ff00"];
  const frame = () => {
    confetti({ particleCount: 6, angle: 60, spread: 70, origin: { x: 0 }, colors, disableForReducedMotion: true });
    confetti({ particleCount: 6, angle: 120, spread: 70, origin: { x: 1 }, colors, disableForReducedMotion: true });
    if (Date.now() < end) requestAnimationFrame(frame);
  };
  frame();
  rain(1.5);
}

function shake() {
  const html = document.documentElement;
  html.classList.remove("shake");
  void html.offsetWidth; // restart animation
  html.classList.add("shake");
  window.setTimeout(() => html.classList.remove("shake"), 900);
}

/** Konami code -> BILLIONAIRE MODE, plus the floating MAKE IT RAIN button. */
export default function BillionaireMode() {
  const [rich, setRich] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const idx = useRef(0);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
      if (key === KONAMI[idx.current]) {
        idx.current++;
        if (idx.current === KONAMI.length) {
          idx.current = 0;
          const on = document.documentElement.classList.toggle("billionaire");
          setRich(on);
          setToast(on ? "BILLIONAIRE MODE ACTIVATED. TAXES: OPTIONAL." : "Billionaire mode off. Welcome back to the 99.9999%.");
          window.setTimeout(() => setToast(null), 3200);
          if (on) {
            shake();
            storm(2500);
            fanfare();
            chaChing();
          }
        }
      } else {
        idx.current = key === KONAMI[0] ? 1 : 0;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const makeItRain = () => {
    rain(rich ? 2 : 1);
    chaChing();
    shake();
  };

  return (
    <>
      <button
        type="button"
        onClick={makeItRain}
        className="fx-rain-btn fixed bottom-5 right-5 z-[65] rounded-full px-5 py-3 font-[family-name:var(--font-display)] text-sm text-black"
        aria-label="Make it rain money confetti"
      >
        💵 MAKE IT RAIN
      </button>
      {toast && (
        <div
          role="status"
          className="fixed left-1/2 top-24 z-[80] -translate-x-1/2 rounded-xl border-2 border-[var(--gold)] bg-black/85 px-6 py-4 text-center font-[family-name:var(--font-display)] text-lg neon"
        >
          {toast}
        </div>
      )}
    </>
  );
}
