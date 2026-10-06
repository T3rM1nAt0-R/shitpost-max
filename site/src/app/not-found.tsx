import Link from "next/link";
import Track404 from "@/components/Track404";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-black px-4 text-center text-white">
      <Track404 />
      <p className="text-xs uppercase tracking-[0.4em] text-pink-400">Error 404 / Press release</p>
      <h1 className="mt-4 bg-gradient-to-r from-yellow-300 via-pink-500 to-cyan-300 bg-clip-text text-5xl font-black text-transparent sm:text-7xl">
        This page was acquired and shut down.
      </h1>
      <p className="mt-6 max-w-xl text-lg text-neutral-300">
        We bought it for $44 billion, fired everyone who worked on it, and replaced it with this
        sentence. Shareholders are thrilled. 🛥️💸
      </p>
      <Link
        href="/"
        className="mt-10 rounded-full border-2 border-yellow-300 px-8 py-3 font-bold uppercase tracking-widest text-yellow-300 transition hover:bg-yellow-300 hover:text-black"
      >
        Return to the empire
      </Link>
    </div>
  );
}
