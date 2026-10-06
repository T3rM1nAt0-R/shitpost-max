"use client";

import { useEffect, useState } from "react";
import { addonsA } from "./batch-a";
import { addonsB } from "./batch-b";
import { ADDON_EVENT, type Addon } from "./types";

const ADDONS: Addon[] = [...addonsA, ...addonsB];

/** Bottom-left "Billionaire Control Panel": every absurd add-on, one tap away. */
export default function Dock() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onTrigger = (e: Event) => {
      const id = (e as CustomEvent<string>).detail;
      ADDONS.find((a) => a.id === id)?.run?.();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener(ADDON_EVENT, onTrigger);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener(ADDON_EVENT, onTrigger);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <>
      {ADDONS.map(({ id, Component }) => (Component ? <Component key={id} /> : null))}
      <div className="fixed bottom-4 left-4 z-[66] flex flex-col items-start gap-2">
        {open && (
          <div
            id="spm-dock"
            className="fx-dock-in max-h-[70vh] w-[min(92vw,26rem)] overflow-y-auto rounded-3xl border-2 border-yellow-300/80 bg-zinc-950/95 p-3 shadow-[0_0_40px_rgba(255,215,0,0.35)]"
          >
            <p className="px-2 pb-2 font-[family-name:var(--font-display)] text-sm text-yellow-300">
              BILLIONAIRE CONTROL PANEL
            </p>
            <ul className="grid grid-cols-2 gap-2">
              {ADDONS.filter((a) => a.run).map((a) => (
                <li key={a.id}>
                  <button
                    type="button"
                    onClick={() => a.run?.()}
                    className="flex h-full w-full flex-col items-start gap-1 rounded-2xl border border-white/10 bg-black/60 p-3 text-left transition-transform hover:-rotate-1 hover:scale-[1.03] hover:border-yellow-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
                  >
                    <span className="text-2xl">{a.emoji}</span>
                    <span className="text-sm font-black uppercase text-white">{a.label}</span>
                    <span className="text-xs text-zinc-400">{a.blurb}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        <button
          type="button"
          aria-expanded={open}
          aria-controls="spm-dock"
          onClick={() => setOpen((o) => !o)}
          className="fx-rain-btn rounded-full px-5 py-3 text-sm font-black uppercase text-black"
        >
          💼 {open ? "Close the vault" : "Control panel"}
        </button>
      </div>
    </>
  );
}
