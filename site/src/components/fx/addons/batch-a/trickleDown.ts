import type { Addon } from "../types";
import { reducedMotion, sadPlink, spawn, toast } from "./util";

let falling = false;

function run() {
  if (falling) {
    toast("Please be patient. The wealth is still trickling.");
    return;
  }
  if (reducedMotion()) {
    sadPlink();
    toast("Wealth has trickled down. Total: $0.01.");
    return;
  }
  falling = true;
  toast("Releasing the wealth. Stand by for prosperity.", 2600);

  const outer = document.createElement("div");
  outer.className = "fxa-penny";
  outer.setAttribute("aria-hidden", "true");
  outer.style.left = `${30 + Math.random() * 40}vw`;
  const inner = document.createElement("span");
  inner.className = "fxa-penny-wobble";
  inner.textContent = "🪙";
  outer.appendChild(inner);
  spawn(outer, 6300);

  window.setTimeout(() => {
    sadPlink();
    toast("Wealth has trickled down. Total: $0.01. Don't spend it all at once.", 4200);
    falling = false;
  }, 6000);
}

export const trickleDownAddon: Addon = {
  id: "trickle-down",
  emoji: "🪙",
  label: "Trickle Down Economics",
  blurb: "Unleash the full force of my generosity. Brace yourself.",
  run,
};
