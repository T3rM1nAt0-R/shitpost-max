import HeroQuote from "./HeroQuote";
import "./feed.css";

const LETTERS = "SHITPOSTMAX".split("");

/** Static hero markup; only the rotating quote is a client island. */
export default function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pb-16 pt-20 text-center sm:pt-28">
      <p className="spm-drop-in relative mb-6 inline-block rounded-full border border-fuchsia-400/60 bg-black/60 px-4 py-1 font-mono text-xs uppercase tracking-[0.3em] text-fuchsia-300 shadow-[0_0_24px_rgba(232,121,249,0.6)]">
        ⚠ Pre-revenue · Post-reality · ∞ Engineers replaced
      </p>

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
        <HeroQuote />
      </div>

      <div className="relative mt-12 flex flex-wrap items-center justify-center gap-4">
        <a
          href="#feed"
          className="spm-cta rounded-2xl bg-gradient-to-r from-fuchsia-500 via-pink-500 to-orange-400 px-8 py-4 text-lg font-black uppercase text-black shadow-[0_0_40px_rgba(236,72,153,0.8)]"
        >
          Browse the fleet 🛥️
        </a>
        <a
          href="/generator"
          className="spm-cta spm-cta-r rounded-2xl border-2 border-cyan-300 bg-black/60 px-8 py-4 text-lg font-black uppercase text-cyan-200 shadow-[0_0_30px_rgba(34,211,238,0.6)]"
        >
          Mint a meme (generator) 🖨️
        </a>
      </div>
    </section>
  );
}
