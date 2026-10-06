import type { Addon } from "../types";
import { landing, whoosh } from "./sound";
import { burst, pick, reducedMotion, toast } from "./util";

const MAX_IN_FLIGHT = 3;
let inFlight = 0;

const AFTERMATH = [
  "Atmosphere: removed (it was slowing us down).",
  "Local microbes have been unionized and then fired.",
  "First Martian Starbucks opens Tuesday. Oat milk: $900.",
  "The red is now a brand color. Trademark pending.",
  "Olympus Mons is now Olympus Mine.",
  "Phobos and Deimos have been rebranded as X1 and X2.",
  "Gravity is 38% of Earth's. So are the wages.",
] as const;

function land() {
  landing();
  void burst({ x: 0.92, y: 0.18 }, ["🔴", "🚩", "💵"], 30);
  toast({
    title: "🪐 MISSION REPORT",
    text: `Mars: acquired. Renamed to X. Rent is due. ${pick(AFTERMATH)}`,
    where: "tr",
    ms: 5200,
    slot: "rocket",
  });
}

function launch() {
  if (inFlight >= MAX_IN_FLIGHT) return;
  whoosh();
  if (reducedMotion()) {
    land();
    return;
  }
  inFlight++;
  const r = document.createElement("span");
  r.className = "fxb-rocket";
  r.setAttribute("aria-hidden", "true");
  r.textContent = "🚀";
  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    inFlight--;
    r.remove();
    land();
  };
  r.addEventListener("animationend", finish, { once: true });
  window.setTimeout(finish, 3000); // safety net if animationend never fires
  document.body.appendChild(r);
}

export const rocketAddon: Addon = {
  id: "launch-rocket-mars",
  emoji: "🚀",
  label: "Launch Rocket to Mars",
  blurb: "Earth had a good run. Time to colonize somewhere without labor laws.",
  run: launch,
};
