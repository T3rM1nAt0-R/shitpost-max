/**
 * Batch B synth sounds. WebAudio oscillators only, created lazily, and every
 * export must only be called from a user-gesture handler.
 */
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

function tone(
  ac: AudioContext,
  freq: number,
  start: number,
  dur: number,
  type: OscillatorType,
  vol: number,
  endFreq?: number,
) {
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  if (endFreq) osc.frequency.exponentialRampToValueAtTime(endFreq, start + dur);
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(vol, start + Math.min(0.04, dur / 3));
  gain.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(gain).connect(ac.destination);
  osc.start(start);
  osc.stop(start + dur + 0.05);
}

/** Ascending acquisition arpeggio (copy of the site fanfare, plus a victory chord). */
export function fanfare() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  [523.25, 659.25, 783.99, 1046.5, 1318.5].forEach((f, i) =>
    tone(ac, f, t + i * 0.09, 0.4, "sawtooth", 0.05),
  );
  [1046.5, 1318.5, 1568].forEach((f) => tone(ac, f, t + 0.5, 0.9, "triangle", 0.05));
}

/** Rocket whoosh: a rising sawtooth sweep with a low rumble under it. */
export function whoosh() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 90, t, 1.4, "sawtooth", 0.06, 1400);
  tone(ac, 55, t, 1.1, "square", 0.04, 35);
  tone(ac, 180, t + 0.05, 1.2, "triangle", 0.04, 2400);
}

/** Soft touchdown blip. */
export function landing() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 880, t, 0.15, "sine", 0.08);
  tone(ac, 1320, t + 0.12, 0.35, "sine", 0.07);
}

/** A butler clearing his throat, disapprovingly. */
export function ahem() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 196, t, 0.12, "square", 0.05, 170);
  tone(ac, 147, t + 0.16, 0.22, "square", 0.05, 120);
}

/** Rubber "CLASSIFIED" stamp thud. */
export function stamp() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 120, t, 0.18, "square", 0.12, 40);
  tone(ac, 60, t, 0.25, "sine", 0.15, 30);
}

/** Tiny bloop for a hot-take toast. */
export function bloop() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 660, t, 0.12, "sine", 0.05, 990);
}
