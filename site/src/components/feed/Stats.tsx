import { getFleetWithStats, totalEngineersReplaced, totalValuation } from "@/lib/fleet";
import CountUp from "./CountUp";
import "./feed.css";

type Stat =
  | { label: string; kind: "count"; to: number; suffix?: string }
  | { label: string; kind: "money"; to: number }
  | { label: string; kind: "static"; value: string };

/** Static stats grid; only the animated numbers are client islands. */
export default function Stats() {
  const stats: Stat[] = [
    { label: "Microservices (one-person, zero people)", kind: "count", to: getFleetWithStats().length },
    { label: "Fleet valuation (audited by vibes)", kind: "money", to: totalValuation() },
    { label: "Engineers replaced (lower bound)", kind: "count", to: totalEngineersReplaced() },
    { label: "Engineer multiplier", kind: "count", to: 1_000_000, suffix: "x" },
    { label: "Problems solved that existed", kind: "static", value: "0" },
    { label: "Yachts per microservice", kind: "static", value: "∞" },
  ];

  return (
    <section className="mx-auto grid max-w-7xl grid-cols-2 gap-4 px-4 py-12 md:grid-cols-3 lg:grid-cols-6">
      {stats.map((s) => (
        <div
          key={s.label}
          className="spm-stat rounded-2xl border border-white/10 bg-gradient-to-br from-zinc-900 to-black p-4 text-center shadow-[0_0_24px_rgba(34,211,238,0.25)]"
        >
          <div className="break-words bg-gradient-to-r from-cyan-300 via-fuchsia-400 to-yellow-300 bg-clip-text font-mono text-xl font-black text-transparent sm:text-2xl">
            {s.kind === "static" ? (
              <span data-money>{s.value}</span>
            ) : s.kind === "money" ? (
              <CountUp to={s.to} money />
            ) : (
              <CountUp to={s.to} suffix={s.suffix} />
            )}
          </div>
          <div className="mt-2 text-xs uppercase tracking-wider text-zinc-400">{s.label}</div>
        </div>
      ))}
    </section>
  );
}
