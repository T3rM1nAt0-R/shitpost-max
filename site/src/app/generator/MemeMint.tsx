"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import confetti from "canvas-confetti";
import { TEMPLATES, generateShitpost, getTemplate } from "@/lib/generator";

const SIZE = 800;
const IMPACT = 'Impact, "Anton", "Arial Black", "Haettenschweiler", sans-serif';

const STICKER_SPOTS = [
  { left: "8%", top: "38%", rot: -18 },
  { left: "74%", top: "30%", rot: 14 },
  { left: "42%", top: "52%", rot: 6 },
];

function wrapLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let line = "";
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function drawMeme(
  canvas: HTMLCanvasElement,
  opts: { templateId: string; top: string; bottom: string; fontSize: number },
) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const t = getTemplate(opts.templateId);
  canvas.width = SIZE;
  canvas.height = SIZE;

  const grad = ctx.createLinearGradient(0, 0, SIZE, SIZE);
  t.stops.forEach((c, i) => grad.addColorStop(i / (t.stops.length - 1), c));
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, SIZE, SIZE);

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  t.stickers.forEach((s, i) => {
    const spot = STICKER_SPOTS[i % STICKER_SPOTS.length];
    ctx.save();
    ctx.translate((parseFloat(spot.left) / 100) * SIZE + 80, (parseFloat(spot.top) / 100) * SIZE + 80);
    ctx.rotate((spot.rot * Math.PI) / 180);
    ctx.font = `140px "Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif`;
    ctx.fillText(s, 0, 0);
    ctx.restore();
  });

  // Preview is ~400px wide; scale font for the 800px export.
  const px = opts.fontSize * 2;
  ctx.font = `${px}px ${IMPACT}`;
  ctx.fillStyle = "#fff";
  ctx.strokeStyle = "#000";
  ctx.lineWidth = Math.max(4, px / 8);
  ctx.lineJoin = "round";
  const maxW = SIZE - 60;
  const lh = px * 1.05;

  const drawBlock = (text: string, anchor: "top" | "bottom") => {
    const lines = wrapLines(ctx, text.toUpperCase(), maxW);
    const startY = anchor === "top" ? 30 + lh / 2 : SIZE - 30 - lh / 2 - (lines.length - 1) * lh;
    lines.forEach((l, i) => {
      ctx.strokeText(l, SIZE / 2, startY + i * lh);
      ctx.fillText(l, SIZE / 2, startY + i * lh);
    });
  };
  drawBlock(opts.top, "top");
  drawBlock(opts.bottom, "bottom");

  ctx.font = `20px ${IMPACT}`;
  ctx.lineWidth = 3;
  ctx.textAlign = "right";
  ctx.strokeText("SHITPOSTMAX.COM", SIZE - 16, SIZE - 14);
  ctx.fillText("SHITPOSTMAX.COM", SIZE - 16, SIZE - 14);
}

const outlined = {
  fontFamily: IMPACT,
  color: "#fff",
  WebkitTextStroke: "2px #000",
  textShadow: "3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000",
  lineHeight: 1.05,
} as const;

export default function MemeMint() {
  const initial = generateShitpost(20260101);
  const [templateId, setTemplateId] = useState(initial.template);
  const [top, setTop] = useState(initial.top);
  const [bottom, setBottom] = useState(initial.bottom);
  const [fontSize, setFontSize] = useState(36);
  const [wobble, setWobble] = useState(true);
  const [mints, setMints] = useState(0);

  const tpl = getTemplate(templateId);

  function shitpostMe() {
    const seed = Math.floor(Math.random() * 2 ** 32);
    const p = generateShitpost(seed);
    setTop(p.top);
    setBottom(p.bottom);
    setTemplateId(p.template);
    setMints((m) => m + 1);
    confetti({
      particleCount: 160,
      spread: 90,
      origin: { y: 0.7 },
      colors: ["#ffd700", "#ff00aa", "#00ffea", "#ffffff"],
    });
  }

  function download() {
    const canvas = document.createElement("canvas");
    drawMeme(canvas, { templateId, top, bottom, fontSize });
    const a = document.createElement("a");
    a.href = canvas.toDataURL("image/png");
    a.download = `shitpostmax-${templateId}-${Date.now()}.png`;
    a.click();
  }

  return (
    <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,22rem)]">
      <div className="flex justify-center">
        <motion.div
          animate={wobble ? { rotate: [-2, 2, -2], scale: [1, 1.015, 1] } : { rotate: 0, scale: 1 }}
          transition={wobble ? { duration: 2.4, repeat: Infinity, ease: "easeInOut" } : { duration: 0.3 }}
          className="relative aspect-square w-full max-w-[400px] overflow-hidden rounded-2xl border-4 border-yellow-300 shadow-[0_0_60px_rgba(255,0,170,0.5)]"
          style={{ background: tpl.background }}
          aria-label="Meme preview"
        >
          {tpl.stickers.map((s, i) => {
            const spot = STICKER_SPOTS[i % STICKER_SPOTS.length];
            return (
              <span
                key={`${tpl.id}-${i}`}
                aria-hidden
                className="pointer-events-none absolute select-none text-7xl"
                style={{ left: spot.left, top: spot.top, transform: `rotate(${spot.rot}deg)` }}
              >
                {s}
              </span>
            );
          })}
          <p
            className="absolute inset-x-3 top-3 break-words text-center uppercase"
            style={{ ...outlined, fontSize }}
          >
            {top}
          </p>
          <p
            className="absolute inset-x-3 bottom-3 break-words text-center uppercase"
            style={{ ...outlined, fontSize }}
          >
            {bottom}
          </p>
        </motion.div>
      </div>

      <div className="space-y-5 rounded-2xl border border-pink-500/40 bg-neutral-950 p-5">
        <fieldset>
          <legend className="mb-2 text-sm font-bold uppercase tracking-widest text-yellow-300">
            Asset class
          </legend>
          <div className="grid grid-cols-3 gap-2">
            {TEMPLATES.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTemplateId(t.id)}
                aria-pressed={t.id === templateId}
                title={t.name}
                className={`flex aspect-square items-center justify-center rounded-lg text-3xl transition hover:scale-105 ${
                  t.id === templateId ? "ring-4 ring-yellow-300" : "ring-1 ring-white/20"
                }`}
                style={{ background: t.background }}
              >
                <span aria-hidden>{t.stickers[0]}</span>
                <span className="sr-only">{t.name}</span>
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-neutral-400">Selected: {tpl.name}</p>
        </fieldset>

        <label className="block text-sm">
          <span className="font-bold uppercase tracking-widest text-yellow-300">Top text</span>
          <input
            value={top}
            onChange={(e) => setTop(e.target.value)}
            className="mt-1 w-full rounded-md border border-white/20 bg-black px-3 py-2 text-white"
          />
        </label>
        <label className="block text-sm">
          <span className="font-bold uppercase tracking-widest text-yellow-300">Bottom text</span>
          <input
            value={bottom}
            onChange={(e) => setBottom(e.target.value)}
            className="mt-1 w-full rounded-md border border-white/20 bg-black px-3 py-2 text-white"
          />
        </label>

        <label className="block text-sm">
          <span className="font-bold uppercase tracking-widest text-yellow-300">
            Font size: {fontSize}px
          </span>
          <input
            type="range"
            min={18}
            max={64}
            value={fontSize}
            onChange={(e) => setFontSize(Number(e.target.value))}
            className="mt-2 w-full accent-pink-500"
          />
        </label>

        <label className="flex items-center gap-3 text-sm">
          <input
            type="checkbox"
            checked={wobble}
            onChange={(e) => setWobble(e.target.checked)}
            className="h-5 w-5 accent-pink-500"
          />
          <span className="font-bold uppercase tracking-widest text-yellow-300">
            Market volatility (wobble)
          </span>
        </label>

        <motion.button
          type="button"
          onClick={shitpostMe}
          whileHover={{ scale: 1.05, rotate: -1 }}
          whileTap={{ scale: 0.92 }}
          className="w-full rounded-xl bg-gradient-to-r from-pink-500 via-fuchsia-500 to-yellow-400 px-4 py-4 text-2xl font-black text-black shadow-[0_0_30px_rgba(255,0,170,0.6)]"
        >
          SHITPOST ME 🚀
        </motion.button>
        <button
          type="button"
          onClick={download}
          className="w-full rounded-xl border-2 border-yellow-300 px-4 py-3 font-bold uppercase tracking-widest text-yellow-300 transition hover:bg-yellow-300 hover:text-black"
        >
          Download PNG 💾
        </button>
        <p className="text-center text-xs text-neutral-500">
          Memes minted this session: {mints.toLocaleString()} (valued at ${(mints * 4.2).toFixed(1)}B)
        </p>
      </div>
    </div>
  );
}
