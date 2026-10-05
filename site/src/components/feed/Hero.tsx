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
      {/* neon blobs */}
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-fuchsia-600/40 blur-3xl"
        animate={{ x: [0, 120, -40, 0], y: [0, 60, 140, 0], scale: [1, 1.3, 0.9, 1] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute -right-32 top-10 h-[28rem] w-[28rem] rounded-full bg-cyan-500/30 blur-3xl"
        animate={{ x: [0, -140, 30, 0], y: [0, 100, -30, 0], scale: [1.1, 0.8, 1.2, 1.1] }}
        transition={{ duration: 17, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-yellow-400/20 blur-3xl"
        animate={{ x: [0, 80, -100, 0], scale: [1, 1.4, 1] }}
        transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
      />

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
          <motion.span
            key={idx}
            className="inline-block bg-clip-text text-transparent"
            style={{
              backgroundImage:
                "linear-gradient(90deg,#ff00e5,#ff7a00,#ffe600,#00ff94,#00d4ff,#7a5cff,#ff00e5)",
              backgroundSize: "400% 100%",
              filter: "drop-shadow(0 0 18px rgba(255,0,229,0.55))",
            }}
            initial={{ y: 120, opacity: 0, rotate: -30 }}
            animate={{
              y: [0, -14, 0],
              opacity: 1,
              rotate: [0, idx % 2 ? 4 : -4, 0],
              backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
            }}
            transition={{
              y: { duration: 2.2, repeat: Infinity, delay: idx * 0.09, ease: "easeInOut" },
              rotate: { duration: 2.2, repeat: Infinity, delay: idx * 0.09, ease: "easeInOut" },
              backgroundPosition: { duration: 6, repeat: Infinity, ease: "linear" },
              opacity: { duration: 0.4, delay: idx * 0.05 },
            }}
            whileHover={{ scale: 1.4, rotate: 360, transition: { duration: 0.6 } }}
          >
            {ch}
          </motion.span>
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
            initial={{ opacity: 0, y: 30, rotateX: 90, filter: "blur(8px)" }}
            animate={{ opacity: 1, y: 0, rotateX: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -30, rotateX: -90, filter: "blur(8px)" }}
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
