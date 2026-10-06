const HEADLINES = [
  "BREAKING: Local billionaire buys the concept of Tuesday, renames it 'Founder Day'",
  "Visionary CEO fires entire company to 'free them up for their next chapter' (unemployment)",
  "Rocket launch #47 confirms Earth is still round; investors demand recount",
  "Tech mogul announces AI that replaces his feelings — 'finally, a 10x improvement'",
  "Yacht too small: billionaire commissions a support yacht for his support yacht",
  "Man worth $400B tweets 'work harder' at 3am from a private island",
  "New startup disrupts water by putting it in a subscription",
  "Billionaire donates $1, receives $40M tax write-off, press calls it 'historic generosity'",
  "SHITPOSTMAX valuation hits $1 quadrillion after pivoting to the blockchain of vibes",
  "Breaking: we have achieved 1000000x engineering on a problem that does not exist",
];

/** Fixed top "breaking news" marquee with billionaire flex headlines. */
export default function NewsTicker() {
  const items = [...HEADLINES, ...HEADLINES];
  return (
    <div
      role="marquee"
      aria-label="Breaking news"
      className="fixed inset-x-0 top-0 z-50 flex h-8 items-center overflow-hidden border-b border-[var(--hot-pink)] bg-black/90 text-xs sm:text-sm"
    >
      <span className="fx-live relative z-10 flex h-full shrink-0 items-center bg-[var(--hot-pink)] px-3 font-[family-name:var(--font-display)] text-black">
        🔴 BREAKING
      </span>
      <div className="relative flex-1 overflow-hidden">
        <div className="marquee flex w-max gap-10 whitespace-nowrap pl-6">
          {items.map((h, i) => (
            <span key={i} aria-hidden={i >= HEADLINES.length} className="text-[var(--gold)]">
              <span className="text-[var(--cyan)]">◆</span> {h}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
