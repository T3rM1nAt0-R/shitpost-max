import type { Metadata } from "next";
import MemeMint from "./MemeMint";

export const metadata: Metadata = {
  title: "Meme Mint",
  description:
    "Mint premium billionaire shitposts. Every meme is pre-acquired, fully leveraged, and 100% tax deductible.",
};

export default function GeneratorPage() {
  return (
    <div className="min-h-screen bg-black px-4 py-10 text-white sm:px-8">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs uppercase tracking-[0.4em] text-pink-400">
          SHITPOSTMAX Treasury Department
        </p>
        <h1 className="mt-2 bg-gradient-to-r from-yellow-300 via-pink-500 to-cyan-300 bg-clip-text text-5xl font-black text-transparent sm:text-7xl">
          MEME MINT 💸
        </h1>
        <p className="mt-3 max-w-2xl text-neutral-300">
          The world&apos;s most expensive free meme generator. We printed these
          memes with the same machine we use to print money.
        </p>
        <MemeMint />
      </div>
    </div>
  );
}
