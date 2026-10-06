import fleetNames from "./fleet.json";

export const REPO_URL = "https://github.com/T3rM1nAt0-R/shitpost-max";

export interface FleetService {
  slug: string;
  name: string;
  emoji: string;
  valuation: number;
  tagline: string;
  url: string;
}

export interface FleetServiceStats extends FleetService {
  engineersReplaced: number;
  baseScore: number;
  ticker: string;
  change: number;
}

/** FNV-1a 32-bit hash. Deterministic, so SSR/static output matches the client. */
export function hashString(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** mulberry32 PRNG seeded from a number. */
export function seededRandom(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick<T>(rand: () => number, arr: readonly T[]): T {
  return arr[Math.floor(rand() * arr.length) % arr.length];
}

const UNITS: readonly [number, string][] = [
  [1e33, "decillion"],
  [1e30, "nonillion"],
  [1e27, "octillion"],
  [1e24, "septillion"],
  [1e21, "sextillion"],
  [1e18, "quintillion"],
  [1e15, "quadrillion"],
  [1e12, "trillion"],
  [1e9, "billion"],
  [1e6, "million"],
  [1e3, "thousand"],
];

/** Format a dollar amount with billionaire-grade unit names, e.g. "$4.2 quadrillion". */
export function formatValuation(n: number): string {
  if (!Number.isFinite(n)) return n < 0 ? "-$∞" : "$∞";
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (abs >= 1e36) return `${sign}$${abs.toExponential(1).replace("+", "")} (we ran out of words)`;
  for (const [value, word] of UNITS) {
    if (abs >= value) {
      const scaled = abs / value;
      const str = scaled >= 100 ? Math.round(scaled).toString() : (Math.round(scaled * 10) / 10).toString();
      return `${sign}$${str} ${word}`;
    }
  }
  return `${sign}$${Math.round(abs)}`;
}

/** Turn "pi-spigot" into "Pi Spigot". */
export function prettifyName(slug: string): string {
  return slug
    .split("-")
    .map((w) => {
      if (/^(api|aqi|ai|ui|id|url|cpu|gpu|dns|ip|io|qr|btc|eth|ssl|tls|json|csv|http)$/i.test(w)) return w.toUpperCase();
      if (/^\d+x$/i.test(w)) return w.toLowerCase();
      return w.charAt(0).toUpperCase() + w.slice(1);
    })
    .join(" ");
}

const CATEGORY_EMOJI: readonly [RegExp, string][] = [
  [/pi|sqrt|prime|fibonacci|aliquot|collatz|math|number|digit|euler|mandel|fractal|babylon/i, "🥧"],
  [/bitcoin|btc|eth|crypto|coin|fee|price|stock|market|balance|money|tax/i, "💸"],
  [/aurora|asteroid|moon|sun|space|star|orbit|planet|iss|comet|meteor/i, "🚀"],
  [/aqi|weather|rain|temp|climate|tide|wind|air/i, "🌪️"],
  [/engineer|agile|meeting|standup|jira|manager|scrum|10x/i, "🧠"],
  [/backup|witness|snapshot|diff|monitor|watch|uptime|status|check/i, "👁️"],
  [/heap|bloom|tree|sort|graph|hash|queue|stack|filter|demo/i, "🧮"],
  [/anagram|acronym|word|text|name|poem|haiku|lorem|emoji|joke/i, "🔤"],
  [/birthday|paradox|random|dice|lottery|chaos/i, "🎲"],
  [/base|convert|encode|decode|binary|hex/i, "🔁"],
];

const FALLBACK_EMOJI = ["🛸", "🦄", "🧨", "💎", "🛥️", "🏝️", "🪐", "🦖", "🗿", "🤑", "👑", "🔥"] as const;

export function categoryEmoji(slug: string): string {
  for (const [re, e] of CATEGORY_EMOJI) if (re.test(slug)) return e;
  return FALLBACK_EMOJI[hashString(slug) % FALLBACK_EMOJI.length];
}

const OPENERS = [
  "I personally acquired",
  "My family office now owns",
  "We 1000000x'd",
  "My cron job's cron job runs",
  "I put on my third yacht",
  "Our board of AIs unanimously approved",
  "I tweeted and accidentally IPO'd",
  "My butler's butler maintains",
  "We vertically integrated",
  "I bought the moon to host",
  "Synergy-maxxed and disrupted",
  "I fired ∞ engineers and kept",
] as const;

const MIDDLES = [
  "{name}, a solution to a problem that never existed",
  "{name} — now with blockchain-grade irrelevance",
  "{name}, which commits to itself more than my ex did",
  "{name} at a {mult}x premium to reality",
  "{name}, Series ∞ funded by my other companies",
  "{name}, so lean it has a negative headcount",
  "{name} and renamed it twice before lunch",
  "{name}, the only microservice with a private jet",
  "{name}, deployed to {n} continents including 2 I invented",
  "{name}, a one-person team of zero people",
] as const;

const CLOSERS = [
  "Problems solved: 0. Vibes: immaculate.",
  "Engineers consulted: none. Lawyers: several.",
  "Revenue is a social construct.",
  "Don't ask about the burn rate.",
  "It runs on pure hubris and a free tier.",
  "Tax-deductible as a philanthropic experiment.",
  "Patent pending in 3 galaxies.",
  "Roadmap: acquire roadmap.",
  "Yes, it is self-aware. No, it doesn't care.",
  "Our SLA is a strongly worded tweet.",
] as const;

export function makeTagline(slug: string, name: string): string {
  const rand = seededRandom(hashString(`tagline:${slug}`));
  const mult = Math.floor(rand() * 9000) + 1000;
  const n = Math.floor(rand() * 5) + 8;
  const middle = pick(rand, MIDDLES)
    .replace("{name}", name)
    .replace("{mult}", mult.toLocaleString("en-US"))
    .replace("{n}", String(n));
  return `${pick(rand, OPENERS)} ${middle}. ${pick(rand, CLOSERS)}`;
}

export function makeTicker(slug: string): string {
  const letters = slug.replace(/[^a-z0-9]/gi, "").toUpperCase();
  const parts = slug.split("-").filter(Boolean);
  const initials = parts.map((p) => p[0]).join("").toUpperCase();
  const t = initials.length >= 3 ? initials : (initials + letters.slice(1)).slice(0, 4);
  return `$${t.slice(0, 5)}`;
}

function buildService(slug: string): FleetServiceStats {
  const rand = seededRandom(hashString(slug));
  const name = prettifyName(slug);
  // Valuation: mantissa 1-9.9 times 10^(12..32). Absolutely audited.
  const exponent = 12 + Math.floor(rand() * 21);
  const mantissa = 1 + Math.floor(rand() * 90) / 10;
  const valuation = mantissa * Math.pow(10, exponent);
  const engineersReplaced = Math.floor(rand() * 999_000) + 1_000;
  const baseScore = Math.floor(rand() * 4200) - 69;
  const change = Math.round((rand() * 2000 - 300) * 10) / 10;
  return {
    slug,
    name,
    emoji: categoryEmoji(slug),
    valuation,
    tagline: makeTagline(slug, name),
    url: `${REPO_URL}/tree/main/${slug}`,
    engineersReplaced,
    baseScore,
    ticker: makeTicker(slug),
    change,
  };
}

let cache: FleetServiceStats[] | null = null;

/** Full fleet with extra fake stats (engineers replaced, seeded score, ticker). */
export function getFleetWithStats(): FleetServiceStats[] {
  if (!cache) {
    const names = (fleetNames as unknown as string[]).filter((n): n is string => typeof n === "string" && n.length > 0);
    cache = Array.from(new Set(names)).map(buildService);
  }
  return cache;
}

/** The fleet: {slug,name,emoji,valuation,tagline,url}[]. Deterministic. */
export function getFleet(): FleetService[] {
  return getFleetWithStats().map(({ slug, name, emoji, valuation, tagline, url }) => ({
    slug,
    name,
    emoji,
    valuation,
    tagline,
    url,
  }));
}

export function totalValuation(): number {
  return getFleetWithStats().reduce((s, f) => s + f.valuation, 0);
}

export function totalEngineersReplaced(): number {
  return getFleetWithStats().reduce((s, f) => s + f.engineersReplaced, 0);
}
