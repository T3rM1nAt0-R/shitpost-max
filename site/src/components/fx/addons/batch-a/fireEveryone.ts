import type { Addon } from "../types";
import { firedBuzzer, pick, reducedMotion, rehireChime, toast } from "./util";

const LAYOFF_TOASTS = [
  "Laid off 187 microservices. Stock up 12%.",
  "Restructured the entire feed. Synergy achieved. Stock up 12%.",
  "Everyone is fired. Except me. I'm the culture. Stock up 12%.",
];
const REHIRE_TOASTS = [
  "Rehired everyone as contractors. No benefits. Same desks.",
  "Turns out the cards did things. Rehired at 60% salary.",
  "Rehired. We're a family. Families don't get equity.",
];

let busy = false;

function run() {
  if (busy) return;
  firedBuzzer();
  toast(pick(LAYOFF_TOASTS));
  if (reducedMotion()) return;

  const vh = window.innerHeight;
  const victims = Array.from(document.querySelectorAll<HTMLElement>(".fx-card"))
    .filter((el) => {
      const r = el.getBoundingClientRect();
      return r.bottom > 0 && r.top < vh && r.width > 0;
    })
    .slice(0, 24);
  if (!victims.length) {
    toast("Nobody on screen to fire. Fired the HR department preemptively.");
    return;
  }

  busy = true;
  victims.forEach((el, i) => {
    el.style.setProperty("--fxa-rot", `${Math.round(Math.random() * 140 - 70)}deg`);
    el.style.setProperty("--fxa-delay", `${i * 60}ms`);
    el.classList.remove("fxa-rehired");
    el.classList.add("fxa-fired");
  });

  window.setTimeout(() => {
    rehireChime();
    toast(pick(REHIRE_TOASTS));
    victims.forEach((el, i) => {
      el.style.setProperty("--fxa-delay", `${i * 40}ms`);
      el.classList.remove("fxa-fired");
      el.classList.add("fxa-rehired");
    });
    window.setTimeout(() => {
      victims.forEach((el) => {
        el.classList.remove("fxa-rehired");
        el.style.removeProperty("--fxa-rot");
        el.style.removeProperty("--fxa-delay");
      });
      busy = false;
    }, 800 + victims.length * 40);
  }, 4000);
}

export const fireEveryoneAddon: Addon = {
  id: "fire-everyone",
  emoji: "🔥",
  label: "Fire Everyone",
  blurb: "Efficiency. Have an intern explain it. Wait, they're gone.",
  run,
};
