"use client";

import { useEffect } from "react";
import type { Addon } from "../types";
import { bloop } from "./sound";
import { persisted, pick, toast, usePersisted } from "./util";

const INTERVAL_MS = 25_000;
const muted = persisted("fxb-hottakes-muted");

const SPEAKERS = [
  "🚀 A billionaire",
  "🛥️ Another billionaire",
  "🏝️ Billionaire (on his island)",
  "🪐 Billionaire (in orbit)",
  "🦖 Billionaire (cloned)",
  "🧘 Billionaire (post-ayahuasca)",
  "🏰 Billionaire (from the bunker)",
  "🤖 Billionaire's AI clone",
] as const;

export const HOT_TAKES = [
  "Poverty is just a mindset. I know because I bought the mindset and shut it down.",
  "I don't wake up early. Early wakes up when I'm ready.",
  "Money can't buy happiness, which is why I bought the company that makes happiness.",
  "Have you tried just inheriting a mine?",
  "I'm basically a self-made man. My father only gave me the self.",
  "Weekends are a bug. I've filed a ticket with the Earth.",
  "My carbon footprint is offset by the fact that I'm emotionally a tree.",
  "I don't pay taxes. Taxes pay me a small fee to be near me.",
  "Water is overrated. I hydrate with liquidity.",
  "Every yacht needs a smaller yacht. That yacht needs a helicopter. That's just physics.",
  "Empathy doesn't scale. I tested it on 40,000 employees.",
  "I read one book a day. The book is my bank statement. It's thrilling.",
  "Sleep is for people whose dreams aren't already acquired.",
  "The sun is a 4.6-billion-year-old startup with zero revenue. I'd short it.",
  "If you're not dying on Mars, are you even really living on Earth?",
  "I don't follow trends. Trends file an NDA and follow me.",
  "Rent is just a subscription to a building I could personally afford 40,000 of.",
  "I asked my lawyer if I'm above the law. He said 'technically you own the law firm.'",
  "Hard work pays off. Specifically, other people's hard work pays off my third superyacht.",
  "I'm not out of touch. I touched a normal person once. Wealth manager says it's fine.",
  "My morning routine: cold plunge, 5 minutes of gratitude for compound interest, layoffs.",
  "I don't have enemies. I have acquisitions that haven't happened yet.",
  "The moon is just a bad Mars. Bought it anyway. Reflexes.",
  "Philanthropy is when you give back 0.0004% and get a hospital wing named after you. Win-win.",
  "I'm thinking of buying democracy, but the reviews are mixed.",
  "Why have a personality when you can have a portfolio?",
  "Ten thousand hours to mastery? I bought someone else's ten thousand hours.",
  "Inflation is just everyone else being bad at being rich.",
  "I don't ask for forgiveness OR permission. I ask for a board seat.",
  "Grass? I don't touch it. I have it flown in and someone touches it on my behalf.",
] as const;

function showTake() {
  bloop();
  const isMuted = muted.get() === "1";
  toast({
    title: pick(SPEAKERS),
    text: pick(HOT_TAKES),
    where: "br",
    bubble: true,
    ms: 9000,
    slot: "hottake",
    action: isMuted
      ? { label: "🔊 Unmute the elite", onClick: () => muted.set(null) }
      : { label: "🔇 Mute the elite", onClick: () => muted.set("1") },
  });
}

function showTakeQuiet() {
  // Timer-driven: no sound (no user gesture), and only while the tab is visible.
  if (document.visibilityState !== "visible") return;
  toast({
    title: pick(SPEAKERS),
    text: pick(HOT_TAKES),
    where: "br",
    bubble: true,
    ms: 9000,
    slot: "hottake",
    action: { label: "🔇 Mute the elite", onClick: () => muted.set("1") },
  });
}

/** Every ~25s (tab visible, not muted) a billionaire shares a take nobody asked for. */
function HotTakes() {
  const isMuted = usePersisted(muted) === "1";

  useEffect(() => {
    if (isMuted) return;
    const id = window.setInterval(showTakeQuiet, INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [isMuted]);

  return null;
}

export const hotTakesAddon: Addon = {
  id: "billionaire-hot-takes",
  emoji: "🌶️",
  label: "Billionaire Hot Takes",
  blurb: "Unsolicited wisdom from people who have never seen a price tag.",
  run: showTake,
  Component: HotTakes,
};
