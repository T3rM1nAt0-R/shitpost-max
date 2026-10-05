import { REPO_URL } from "@/lib/fleet";

const DISCLAIMERS = [
  "Not financial advice. Not engineering advice. Barely advice.",
  "All valuations were computed by a hash function with a trust fund.",
  "No engineers were harmed. They were simply replaced, ∞ times.",
  "Past performance is not indicative of anything, including the present.",
  "π was acquired in an all-stock deal. The digits remain irrational.",
  "Our cron jobs are independent contractors with family offices.",
  "Problems solved that actually existed: 0. We are very proud.",
  "This website is carbon neutral because we bought the concept of carbon.",
];

export default function Footer() {
  return (
    <footer className="border-t-2 border-fuchsia-500/50 bg-black px-4 py-12 text-center">
      <p className="text-2xl font-black text-white">
        SHITPOSTMAX™ — <span className="text-fuchsia-400">1000000x engineer</span> energy
      </p>
      <ul className="mx-auto mt-6 grid max-w-4xl gap-2 text-xs text-zinc-500 sm:grid-cols-2">
        {DISCLAIMERS.map((d) => (
          <li key={d}>* {d}</li>
        ))}
      </ul>
      <p className="mt-8 font-mono text-sm">
        <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="text-cyan-300 hover:underline">
          github.com/T3rM1nAt0-R/shitpost-max ↗
        </a>{" "}
        · <a href="/generator" className="text-yellow-300 hover:underline">Mint a meme (generator)</a>
      </p>
      <p className="mt-4 text-[10px] uppercase tracking-[0.4em] text-zinc-700">
        © forever · all rights acquired · reality pending regulatory approval
      </p>
    </footer>
  );
}
