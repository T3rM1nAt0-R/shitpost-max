"use client";

import { AnimatePresence, motion } from "framer-motion";
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

const LETTERS = "SHITPOSTMAX".split("");

export default function Hero() {
  const [i, setI] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => setI((n) => (n + 1) % QUOTES.length), 3200);
    return () => window.clearInterval(id);
  }, []);

  return (
    <section className="relative overflow-hidden px-4 pb-16 pt-20 text-center sm:pt-28">
      <motion.p
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mb-6 inline-block rounded-full border border-fuchsia-400/60 bg-black/60 px-4 py-1 font-mono text-xs uppercase tracking-[0.3em] text-fuchsia-300 shadow-[0_0_24px_rgba(232,121,249,0.6)]"
      >
        ⚠ Pre-revenue · Post-reality · ∞ Engineers replaced
      </motion.p>

      <h1
        className="glitch relative mx-auto flex flex-wrap justify-center select-none font-black leading-none tracking-tighter"
        data-text="SHITPOSTMAX"
        style={{ fontSize: "clamp(3rem, 13vw, 11rem)" }}
      >
        {LETTERS.map((ch, idx) => (
          <span
            key={idx}
            className="fx-letter"
            style={{
              backgroundPosition: `${idx * 10}% 50%`,
              animationDelay: `${idx * 0.09}s`,
            }}
          >
            {ch}
          </span>
        ))}
      </h1>

      <p className="relative mx-auto mt-6 max-w-3xl text-lg text-zinc-300 sm:text-2xl">
        A self-running, self-committing fleet of one-person microservices —{" "}
        <span className="font-bold text-yellow-300">engineering-services energy</span>, applied to{" "}
        <span className="italic text-cyan-300">problems that do not exist</span>.
      </p>

      <div className="relative mx-auto mt-10 flex h-28 max-w-4xl items-center justify-center sm:h-24">
        <AnimatePresence mode="wait">
          <motion.blockquote
            key={i}
            initial={{ opacity: 0, y: 30, rotateX: 90 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            exit={{ opacity: 0, y: -30, rotateX: -90 }}
            transition={{ duration: 0.5 }}
            className="text-xl font-semibold text-white sm:text-3xl"
          >
            <span className="text-fuchsia-400">“</span>
            {QUOTES[i]}
            <span className="text-fuchsia-400">”</span>
            <footer className="mt-2 font-mono text-xs uppercase tracking-widest text-zinc-400">
              — every billionaire, simultaneously, on a group call from 14 yachts
            </footer>
          </motion.blockquote>
        </AnimatePresence>
      </div>

      <div className="relative mt-12 flex flex-wrap items-center justify-center gap-4">
        <motion.a
          href="#feed"
          whileHover={{ scale: 1.08, rotate: -2 }}
          whileTap={{ scale: 0.9 }}
          className="rounded-2xl bg-gradient-to-r from-fuchsia-500 via-pink-500 to-orange-400 px-8 py-4 text-lg font-black uppercase text-black shadow-[0_0_40px_rgba(236,72,153,0.8)]"
        >
          Browse the fleet 🛥️
        </motion.a>
        <motion.a
          href="/generator"
          whileHover={{ scale: 1.08, rotate: 2 }}
          whileTap={{ scale: 0.9 }}
          className="rounded-2xl border-2 border-cyan-300 bg-black/60 px-8 py-4 text-lg font-black uppercase text-cyan-200 shadow-[0_0_30px_rgba(34,211,238,0.6)]"
        >
          Mint a meme (generator) 🖨️
        </motion.a>
      </div>
    </section>
  );
}
