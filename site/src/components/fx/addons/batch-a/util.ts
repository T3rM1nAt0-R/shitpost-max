/* Shared helpers for add-on batch A: reduced-motion check, DOM toast, synth sounds.
 * Everything here is DOM-only and fire-and-forget: nodes are removed when done. */

export function reducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Append a node to <body> and remove it after `ms`. */
export function spawn(el: HTMLElement, ms: number) {
  document.body.appendChild(el);
  window.setTimeout(() => el.remove(), ms);
  return el;
}

export const pick = <T,>(a: readonly T[]): T => a[Math.floor(Math.random() * a.length)];

let toastHost: HTMLDivElement | null = null;

/** Tiny DOM toast, bottom-center above the dock. Auto-dismisses. */
export function toast(message: string, ms = 3600) {
  if (typeof document === "undefined") return;
  if (!toastHost || !toastHost.isConnected) {
    toastHost = document.createElement("div");
    toastHost.className = "fxa-toast-host";
    toastHost.setAttribute("role", "status");
    toastHost.setAttribute("aria-live", "polite");
    document.body.appendChild(toastHost);
  }
  // keep at most 3 on screen
  while (toastHost.childElementCount >= 3) toastHost.firstElementChild?.remove();
  const t = document.createElement("div");
  t.className = "fxa-toast";
  t.style.setProperty("--fxa-toast-ms", `${ms}ms`);
  t.textContent = message;
  toastHost.appendChild(t);
  window.setTimeout(() => {
    t.remove();
    if (toastHost && toastHost.childElementCount === 0) {
      toastHost.remove();
      toastHost = null;
    }
  }, ms);
}

/* ---------- WebAudio (oscillators only; call from a user gesture) ---------- */

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
  gain.gain.exponentialRampToValueAtTime(vol, start + 0.008);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(gain).connect(ac.destination);
  osc.start(start);
  osc.stop(start + dur + 0.05);
}

/** NYSE-style electric bell: a fast clapper hammering an inharmonic bell for ~1.3s. */
export function ipoBell() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  const strikes = 20;
  for (let i = 0; i < strikes; i++) {
    const s = t + i * 0.065;
    tone(ac, 1046, s, 0.35, "sine", 0.04);
    tone(ac, 2489, s, 0.22, "sine", 0.02);
    tone(ac, 3720, s, 0.12, "sine", 0.012);
    tone(ac, 140, s, 0.03, "square", 0.015); // clapper clack
  }
  // final ring-out
  const end = t + strikes * 0.065;
  tone(ac, 1046, end, 1.6, "sine", 0.06);
  tone(ac, 2489, end, 1.1, "sine", 0.025);
}

/** Corporate "you're fired" buzzer: two descending sawtooth blats. */
export function firedBuzzer() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 220, t, 0.28, "sawtooth", 0.06, 150);
  tone(ac, 185, t + 0.32, 0.5, "sawtooth", 0.06, 90);
}

/** Cheerful "rehired" two-note chime. */
export function rehireChime() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 784, t, 0.25, "triangle", 0.05);
  tone(ac, 1175, t + 0.12, 0.4, "triangle", 0.05);
}

/** The world's saddest coin: one tiny, lonely plink. */
export function sadPlink() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 2093, t, 0.18, "triangle", 0.025);
  tone(ac, 1760, t + 0.22, 0.5, "sine", 0.015, 1400);
}

/** Descending slide whistle for the parachute. */
export function slideWhistle() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 1800, t, 1.4, "sine", 0.04, 500);
}

/** Cash-register cha-ching (copied from fx/sound.ts so batch A stays self-contained). */
export function chaChingA() {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime;
  tone(ac, 180, t, 0.06, "square", 0.08);
  tone(ac, 233, t, 0.06, "square", 0.05);
  const partials: Array<[number, number]> = [
    [1318.5, 0.18],
    [1975.5, 0.1],
    [2637, 0.06],
  ];
  for (const [f, v] of partials) tone(ac, f, t + 0.09, 0.9, "sine", v);
}
