import type { Addon } from "../types";
import { chaChingA, ipoBell, pick, reducedMotion, spawn, toast } from "./util";

const TICKERS = ["$YOU", "$YOU", "$YOU", "$ME", "$DADDY", "$GOD"];
const SUBTITLES = [
  "Opened at $4,200. Valued at one (1) vibe.",
  "Revenue: $0. Market cap: yes.",
  "Up 900% on no news. Analysts: 'strong buy, we think?'",
  "Dual-class shares. You get 10,000 votes. Everyone else gets a hat.",
];
const TOASTS = [
  "Ding ding ding. You are now owned by index funds. Act natural.",
  "Congratulations. Your morning routine is now a quarterly earnings call.",
  "You're public. Please stop saying 'pre-revenue' in front of the SEC.",
];

let busy = false;

async function burst() {
  if (reducedMotion()) return;
  const confetti = (await import("canvas-confetti")).default;
  const shapes = ["📈", "💵", "🔔", "🥂"].map((text) => confetti.shapeFromText({ text, scalar: 2 }));
  const fire = (x: number, angle: number) =>
    confetti({
      particleCount: 45,
      angle,
      spread: 75,
      startVelocity: 55,
      scalar: 2,
      shapes,
      origin: { x, y: 0.7 },
      disableForReducedMotion: true,
    });
  fire(0.1, 60);
  fire(0.9, 120);
}

function run() {
  if (busy) return;
  busy = true;
  window.setTimeout(() => {
    busy = false;
  }, 2700);

  ipoBell();
  window.setTimeout(chaChingA, 1400);

  const flash = document.createElement("div");
  flash.className = "fxa-flash";
  flash.setAttribute("aria-hidden", "true");
  spawn(flash, 900);

  const wrap = document.createElement("div");
  wrap.className = "fxa-stamp-wrap";
  wrap.setAttribute("aria-hidden", "true");
  const stamp = document.createElement("div");
  stamp.className = "fxa-stamp";
  const big = document.createElement("span");
  big.className = "fxa-stamp-big";
  big.textContent = `${pick(TICKERS)} IS NOW PUBLIC`;
  const small = document.createElement("span");
  small.className = "fxa-stamp-small";
  small.textContent = pick(SUBTITLES);
  stamp.append(big, small);
  wrap.appendChild(stamp);
  spawn(wrap, 2700);

  void burst();
  toast(pick(TOASTS));
}

export const ipoBellAddon: Addon = {
  id: "ipo-bell",
  emoji: "🔔",
  label: "Ring the IPO Bell",
  blurb: "Go public. Fiduciary duty is a state of mind.",
  run,
};
