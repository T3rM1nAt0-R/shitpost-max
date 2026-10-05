"use client";

import { useEffect, useRef } from "react";

const EMOJI = ["💸", "🚀", "💎", "🤑", "📈", "🪙", "🛥️", "🌕"];
const HUES = [320, 185, 90, 48];

type Particle = {
  x: number;
  y: number;
  z: number; // depth 0.2..1 (parallax + size)
  vy: number;
  spin: number;
  rot: number;
  glyph: string | null; // null = star
  hue: number;
};

/** Full-screen money starfield with mouse parallax. Static frame under reduced motion. */
export default function ParticleField() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let w = 0;
    let h = 0;
    let particles: Particle[] = [];
    const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
    let raf = 0;

    const make = (initial: boolean): Particle => {
      const z = 0.2 + Math.random() * 0.8;
      return {
        x: Math.random() * w,
        y: initial ? Math.random() * h : -40,
        z,
        vy: 0.15 + z * 0.9,
        spin: (Math.random() - 0.5) * 0.02,
        rot: Math.random() * Math.PI * 2,
        glyph: Math.random() < 0.28 ? EMOJI[Math.floor(Math.random() * EMOJI.length)] : null,
        hue: HUES[Math.floor(Math.random() * HUES.length)],
      };
    };

    const resize = () => {
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.round(Math.min(160, (w * h) / 9000));
      particles = Array.from({ length: count }, () => make(true));
      if (reduce) draw(0);
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, w, h);
      mouse.x += (mouse.tx - mouse.x) * 0.06;
      mouse.y += (mouse.ty - mouse.y) * 0.06;
      for (const p of particles) {
        const px = p.x - mouse.x * 40 * p.z;
        const py = p.y - mouse.y * 40 * p.z;
        if (p.glyph) {
          ctx.save();
          ctx.globalAlpha = 0.3 + p.z * 0.5;
          ctx.translate(px, py);
          ctx.rotate(p.rot);
          ctx.font = `${Math.round(10 + p.z * 22)}px serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(p.glyph, 0, 0);
          ctx.restore();
        } else {
          const twinkle = 0.5 + 0.5 * Math.sin(t * 0.003 + p.x);
          ctx.fillStyle = `hsla(${p.hue}, 100%, 70%, ${0.25 + p.z * 0.6 * twinkle})`;
          const s = 0.6 + p.z * 1.8;
          ctx.fillRect(px, py, s, s);
        }
      }
    };

    const tick = (t: number) => {
      for (const p of particles) {
        p.y += p.vy;
        p.rot += p.spin;
        if (p.y > h + 40) Object.assign(p, make(false));
      }
      draw(t);
      raf = requestAnimationFrame(tick);
    };

    const onMove = (e: PointerEvent) => {
      mouse.tx = e.clientX / w - 0.5;
      mouse.ty = e.clientY / h - 0.5;
    };
    const onVis = () => {
      cancelAnimationFrame(raf);
      if (!document.hidden) raf = requestAnimationFrame(tick);
    };

    resize();
    window.addEventListener("resize", resize);
    if (!reduce) {
      window.addEventListener("pointermove", onMove, { passive: true });
      document.addEventListener("visibilitychange", onVis);
      raf = requestAnimationFrame(tick);
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  return <canvas ref={ref} aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10" />;
}
