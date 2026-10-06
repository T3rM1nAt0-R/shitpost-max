/**
 * Deterministic billionaire-voice shitpost generator.
 * Pure functions only: same seed in, same flex out.
 */

export type Shitpost = { top: string; bottom: string; template: string };

export type MemeTemplate = {
  id: string;
  name: string;
  /** CSS background (gradients only, no external images). */
  background: string;
  /** Canvas gradient stops, top to bottom. */
  stops: string[];
  stickers: string[];
};

export const TEMPLATES: MemeTemplate[] = [
  {
    id: "rocket",
    name: "Mars Commute",
    background: "linear-gradient(160deg,#0b0033 0%,#3a0ca3 45%,#ff006e 100%)",
    stops: ["#0b0033", "#3a0ca3", "#ff006e"],
    stickers: ["🚀", "🪐", "🌕"],
  },
  {
    id: "diamond",
    name: "Diamond Hands",
    background: "linear-gradient(135deg,#00f5d4 0%,#00bbf9 50%,#9b5de5 100%)",
    stops: ["#00f5d4", "#00bbf9", "#9b5de5"],
    stickers: ["💎", "🙌", "💎"],
  },
  {
    id: "yacht",
    name: "Yacht Inside A Yacht",
    background: "linear-gradient(180deg,#48cae4 0%,#0077b6 55%,#03045e 100%)",
    stops: ["#48cae4", "#0077b6", "#03045e"],
    stickers: ["🛥️", "🛥️", "🌊"],
  },
  {
    id: "money",
    name: "Liquidity Event",
    background: "linear-gradient(145deg,#1b4332 0%,#2d6a4f 40%,#d4af37 100%)",
    stops: ["#1b4332", "#2d6a4f", "#d4af37"],
    stickers: ["🤑", "💸", "💰"],
  },
  {
    id: "gold",
    name: "Solid Gold Toilet",
    background: "linear-gradient(120deg,#5c3d00 0%,#ffd700 50%,#fff4b8 100%)",
    stops: ["#5c3d00", "#ffd700", "#fff4b8"],
    stickers: ["🏆", "👑", "🚽"],
  },
  {
    id: "neon",
    name: "Hostile Takeover Rave",
    background: "linear-gradient(200deg,#000 0%,#ff00aa 50%,#00ffea 100%)",
    stops: ["#000000", "#ff00aa", "#00ffea"],
    stickers: ["🕺", "📈", "🔥"],
  },
];

const PAIRS: ReadonlyArray<readonly [string, string]> = [
  ["I DIDN'T BUY TWITTER", "TWITTER BOUGHT ME"],
  ["MY YACHT HAS A YACHT", "THAT YACHT HAS A HELIPAD"],
  ["THEY SAID TOUCH GRASS", "SO I BOUGHT MONTANA"],
  ["I DON'T CHECK MY BANK BALANCE", "MY BANK CHECKS ME"],
  ["ROCKET EXPLODED ON LAUNCH", "CALLED IT A RAPID UNSCHEDULED FLEX"],
  ["I DON'T PAY TAXES", "I PAY ACCOUNTANTS TO SAY NO"],
  ["LOST $40 BILLION TODAY", "STILL HAVE MORE BILLIONS"],
  ["MY HOBBY?", "BUYING YOUR HOBBY"],
  ["GOING TO SPACE FOR 11 MINUTES", "BECAUSE EARTH WAS SOLD OUT"],
  ["I DON'T HAVE A PARKING SPOT", "I HAVE A PARKING CITY"],
  ["SOME PEOPLE HAVE A SIDE HUSTLE", "I HAVE A SIDE COUNTRY"],
  ["MY CAR DOESN'T NEED GAS", "IT NEEDS VENTURE CAPITAL"],
  ["I DON'T READ THE NEWS", "I ACQUIRE IT"],
  ["WORK-LIFE BALANCE", "IS WHEN BOTH ARE TAX DEDUCTIBLE"],
  ["DIAMOND HANDS", "DIAMOND EVERYTHING"],
  ["NEVER TRUST A STAIRCASE", "TAKE THE PRIVATE ELEVATOR TO THE PRIVATE JET"],
  ["I DIDN'T CHOOSE THE MOON", "I PRE-ORDERED IT"],
  ["MONEY CAN'T BUY HAPPINESS", "BUT IT BOUGHT THE COMPANY THAT MAKES IT"],
  ["MY BURNER ACCOUNT", "IS A PUBLICLY TRADED COMPANY"],
  ["THEY ASKED FOR MY NET WORTH", "I ASKED FOR A BIGGER CALCULATOR"],
  ["I DON'T GO TO THE GYM", "THE GYM COMES TO MY THIRD ISLAND"],
  ["ALL MY FRIENDS ARE HEDGE FUNDS", "WE HEDGE EACH OTHER"],
  ["POST THIS MEME", "AND I'LL BUY THE INTERNET"],
  ["I'M NOT ON A DIET", "I'M ON A LEVERAGED BUYOUT"],
  ["I DON'T TIP WAITERS", "I TIP RESTAURANTS INTO MY PORTFOLIO"],
  ["MY ALARM CLOCK", "IS A STOCK MARKET OPENING BELL"],
  ["WHAT'S A BUDGET?", "IS IT FOR SALE?"],
  ["I SHITPOST", "THE MARKET MOVES"],
];

const SUBJECTS = [
  "MY THIRD MOON BASE",
  "MY EMOTIONAL SUPPORT YACHT",
  "A GOLDEN TOILET",
  "THE CONCEPT OF WEDNESDAY",
  "A SOCIAL NETWORK",
  "THE OCEAN",
  "MY RIVAL'S LAWN",
  "A ROCKET (USED)",
];

const VERBS = ["BOUGHT", "ACQUIRED", "MINTED", "LAUNCHED", "TOKENIZED", "SHORTED", "FIRED"];

const PUNCHLINES = [
  "BEFORE BREAKFAST",
  "WITH POCKET CHANGE",
  "TO FEEL SOMETHING",
  "AS A TAX WRITE-OFF",
  "BECAUSE IT WAS TUESDAY",
  "AND THEN SHITPOSTED ABOUT IT",
  "FOR THE VIBES. ONLY THE VIBES.",
];

/** mulberry32 PRNG: returns a function producing floats in [0, 1). */
export function seededRandom(seed: number): () => number {
  let a = seed >>> 0;
  return function next() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick<T>(rng: () => number, list: ReadonlyArray<T>): T {
  return list[Math.floor(rng() * list.length)];
}

export function generateShitpost(seed: number): Shitpost {
  const rng = seededRandom(seed);
  const template = pick(rng, TEMPLATES).id;
  if (rng() < 0.7) {
    const [top, bottom] = pick(rng, PAIRS);
    return { top, bottom, template };
  }
  return {
    top: `I ${pick(rng, VERBS)} ${pick(rng, SUBJECTS)}`,
    bottom: pick(rng, PUNCHLINES),
    template,
  };
}

export function getTemplate(id: string): MemeTemplate {
  return TEMPLATES.find((t) => t.id === id) ?? TEMPLATES[0];
}
