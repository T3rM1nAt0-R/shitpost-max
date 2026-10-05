let ctx: AudioContext | null = null;

function audio(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const Ctor =
    window.AudioContext ??
    (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  ctx ??= new Ctor();
  if (ctx.state === "suspended") void ctx.resume();
  return ctx;
}

function ping(
  ac: AudioContext,
  freq: number,
  start: number,
  dur: number,
  type: OscillatorType,
  vol: number,
) {
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(vol, start + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(gain).connect(ac.destination);
  osc.start(start);
  osc.stop(start + dur + 0.05);
}

/** Synthesized cash-register "cha-ching". Only call from a user-gesture handler. */
export function chaChing() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  // "cha": drawer clunk
  ping(ac, 180, t, 0.06, "square", 0.08);
  ping(ac, 233, t, 0.06, "square", 0.05);
  // "ching": bell partials
  const partials: Array<[number, number]> = [
    [1318.5, 0.18],
    [1975.5, 0.1],
    [2637, 0.06],
    [3951, 0.03],
  ];
  for (const [f, v] of partials) ping(ac, f, t + 0.09, 0.9, "sine", v);
  ping(ac, 1568, t + 0.16, 0.7, "triangle", 0.08);
}

/** Ascending arpeggio for BILLIONAIRE MODE. Only call from a user-gesture handler. */
export function fanfare() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  [523.25, 659.25, 783.99, 1046.5, 1318.5].forEach((f, i) =>
    ping(ac, f, t + i * 0.09, 0.4, "sawtooth", 0.05),
  );
}
