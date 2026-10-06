"use client";

import { useEffect, useState } from "react";

const QUOTES = [
  "I acquired π. All of it. Every digit.",
  "My cron job has a family office.",
  "We 1000000x'd problems that don't exist.",
  "I replaced ∞ engineers with a YAML file and a yacht.",
  "Our microservices commit more often than I do to anything.",
  "I bought Mondays. They're optional now. For me.",
  "My servers are carbon neutral because I bought the carbon.",
  "We don't have product-market fit. We have market-product fit. We bought the market.",
  "I tried to short reality but reality was already shorted by my other fund.",
  "Each of my one-person microservices has zero people. That's the efficiency.",
  "I have a Series Z. There is no Series AA. I own the alphabet.",
  "Problems solved that existed: 0. Problems invented, then solved: 187.",
];

const SHOW_MS = 3200;
const OUT_MS = 300;

/** The only client piece of the hero: a rotating quote with CSS flip in/out. */
export default function HeroQuote() {
  const [i, setI] = useState(0);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const t = window.setTimeout(() => setLeaving(true), SHOW_MS - OUT_MS);
    return () => window.clearTimeout(t);
  }, [i]);

  useEffect(() => {
    if (!leaving) return;
    const t = window.setTimeout(() => {
      setLeaving(false);
      setI((n) => (n + 1) % QUOTES.length);
    }, OUT_MS);
    return () => window.clearTimeout(t);
  }, [leaving]);

  return (
    <blockquote
      key={i}
      className={`text-xl font-semibold text-white sm:text-3xl ${leaving ? "spm-quote-out" : "spm-quote-in"}`}
    >
      <span className="text-fuchsia-400">“</span>
      {QUOTES[i]}
      <span className="text-fuchsia-400">”</span>
      <footer className="mt-2 font-mono text-xs uppercase tracking-widest text-zinc-400">
        — every billionaire, simultaneously, on a group call from 14 yachts
      </footer>
    </blockquote>
  );
}
