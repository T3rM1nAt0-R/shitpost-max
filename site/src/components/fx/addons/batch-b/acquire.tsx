"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import type { Addon } from "../types";
import { chaChing } from "../../sound";
import { fanfare } from "./sound";
import { burst, persisted, toast, usePersisted } from "./util";

const OPEN_EVENT = "fxb-acquire-open";
const owner = persisted("fxb-owner");

/** Text only, max 20 chars. Letters, digits, spaces and a little punctuation. */
export function sanitizeName(raw: string): string {
  return raw
    .replace(/[^\p{L}\p{N} .'_-]/gu, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 20)
    .trim();
}

function brand(name: string) {
  return `${name.replace(/[\s.'_-]+/g, "").toUpperCase()}POSTMAX`;
}

/* ---------- DOM rewriting: text nodes only, originals remembered for "Sell it back" ---------- */

const ORIGINAL = /SHITPOSTMAX/g;
const HAS = /SHITPOSTMAX/;
const textOriginals = new Map<Text, string>();
let titleOriginal: string | null = null;
const LOGO = 'nav a[href="/"]';

function rewriteTextNodes(root: Element, replacement: string, wholeIfNoMatch: boolean) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = [];
  for (let n = walker.nextNode(); n; n = walker.nextNode()) nodes.push(n as Text);
  let hit = false;
  for (const node of nodes) {
    const orig = textOriginals.get(node) ?? node.nodeValue ?? "";
    if (!HAS.test(orig)) continue;
    textOriginals.set(node, orig);
    const next = orig.replace(ORIGINAL, replacement);
    if (node.nodeValue !== next) node.nodeValue = next;
    hit = true;
  }
  if (!hit && wholeIfNoMatch) {
    const first = nodes.find((n) => (n.nodeValue ?? "").trim());
    if (first) {
      if (!textOriginals.has(first)) textOriginals.set(first, first.nodeValue ?? "");
      if (first.nodeValue !== replacement) first.nodeValue = replacement;
    }
  }
}

function applyBrand(name: string | null) {
  if (!name) {
    for (const [node, orig] of textOriginals) if (node.isConnected) node.nodeValue = orig;
    textOriginals.clear();
    if (titleOriginal !== null) document.title = titleOriginal;
    titleOriginal = null;
    document.querySelectorAll<HTMLElement>("[data-fxb-orig-text]").forEach((el) => {
      el.setAttribute("data-text", el.dataset.fxbOrigText ?? "");
      delete el.dataset.fxbOrigText;
    });
    return;
  }
  const b = brand(name);
  // Prune nodes React already threw away.
  for (const node of textOriginals.keys()) if (!node.isConnected) textOriginals.delete(node);

  if (!document.title.includes(b)) {
    titleOriginal = document.title;
    document.title = HAS.test(document.title)
      ? document.title.replace(ORIGINAL, b)
      : `${b} | ${document.title}`;
  }
  document.querySelectorAll("[data-site-name]").forEach((el) => rewriteTextNodes(el, b, true));
  const logo = document.querySelector<HTMLElement>(LOGO);
  if (logo) {
    rewriteTextNodes(logo, b, true);
    if (logo.hasAttribute("data-text")) {
      if (logo.dataset.fxbOrigText === undefined) logo.dataset.fxbOrigText = logo.getAttribute("data-text") ?? "";
      logo.setAttribute("data-text", b);
    }
  }
}

/* ---------- component: modal + ribbon + re-apply on load/navigation ---------- */

function AcquireSite() {
  const name = usePersisted(owner);
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const dialogRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const onOpen = () => {
      returnFocus.current = document.activeElement as HTMLElement | null;
      setOpen(true);
    };
    window.addEventListener(OPEN_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_EVENT, onOpen);
  }, []);

  // Re-apply on load, on ownership change and after client-side navigation.
  useEffect(() => {
    applyBrand(name);
    if (!name) return;
    const t = window.setTimeout(() => applyBrand(name), 60);
    // Next rewrites <title> on navigation; keep it ours. Fires only on head changes.
    const mo = new MutationObserver(() => {
      if (!document.title.includes(brand(name))) applyBrand(name);
    });
    mo.observe(document.head, { childList: true, subtree: true, characterData: true });
    return () => {
      window.clearTimeout(t);
      mo.disconnect();
    };
  }, [name, pathname]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const close = () => {
    setOpen(false);
    setDraft("");
    returnFocus.current?.focus?.();
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const clean = sanitizeName(draft);
    if (!clean) {
      inputRef.current?.focus();
      return;
    }
    fanfare();
    owner.set(clean);
    close();
    void burst({ x: 0.5, y: 0.2 }, ["💵", "💼", "🏦", "💸"], 60);
    toast({
      title: "DEAL CLOSED",
      text: `${brand(clean)} acquired for $44,000,000,000. Paid in vibes. The board was not consulted (there is no board).`,
      ms: 5200,
      slot: "acquire",
    });
  };

  const sellBack = () => {
    chaChing();
    owner.set(null);
    toast({
      title: "DIVESTED",
      text: "Sold back for $1 and a firm handshake. Loss: $43,999,999,999. Tax write-off: priceless.",
      ms: 4800,
      slot: "acquire",
    });
  };

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      close();
      return;
    }
    if (e.key !== "Tab" || !dialogRef.current) return;
    const f = dialogRef.current.querySelectorAll<HTMLElement>("input, button");
    if (!f.length) return;
    const first = f[0];
    const last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };

  return (
    <>
      {name && (
        <div className="fxb-ribbon fixed inset-x-0 top-[6.5rem] z-[45] mx-auto flex w-fit max-w-[92vw] items-center gap-3 rounded-full border-2 border-yellow-300 bg-black/90 px-4 py-1.5 text-xs font-black uppercase text-yellow-200 shadow-[0_0_24px_rgba(255,215,0,0.35)]">
          <span>
            Under new management: {name}. Everyone is fired.
          </span>
          <button
            type="button"
            onClick={sellBack}
            className="shrink-0 rounded-full bg-yellow-300 px-2 py-0.5 text-[10px] text-black hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
          >
            Sell it back
          </button>
        </div>
      )}
      {open && (
        <div
          className="fixed inset-0 z-[90] flex items-center justify-center bg-black/80 p-4"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) close();
          }}
        >
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="fxb-acquire-title"
            onKeyDown={onKeyDown}
            className="fxb-pop w-[min(92vw,28rem)] rounded-3xl border-2 border-yellow-300 bg-zinc-950 p-6 text-white shadow-[0_0_60px_rgba(255,215,0,0.35)]"
          >
            <p className="text-4xl">🏦</p>
            <h2
              id="fxb-acquire-title"
              className="mt-2 font-[family-name:var(--font-display)] text-xl text-yellow-300"
            >
              Enter your name to acquire SHITPOSTMAX for $44B
            </h2>
            <p className="mt-2 text-sm text-zinc-400">
              No due diligence. No refunds. Financing secured (I said so in a post). Your
              name goes on the logo; the employees go in the river.
            </p>
            <form onSubmit={onSubmit} className="mt-4 flex flex-col gap-3">
              <label htmlFor="fxb-acquire-name" className="text-xs font-black uppercase text-zinc-300">
                Acquirer (max 20 chars)
              </label>
              <input
                id="fxb-acquire-name"
                ref={inputRef}
                value={draft}
                maxLength={20}
                autoComplete="off"
                spellCheck={false}
                onChange={(e) => setDraft(e.target.value.slice(0, 20))}
                placeholder="e.g. ELON, JEFF, A RACCOON"
                className="rounded-xl border border-white/20 bg-black px-3 py-2 text-lg font-black uppercase text-white outline-none focus:border-yellow-300"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="submit"
                  className="fx-rain-btn rounded-full px-5 py-2 text-sm font-black uppercase text-black"
                >
                  💸 Wire $44B
                </button>
                <button
                  type="button"
                  onClick={close}
                  className="rounded-full border border-white/20 px-4 py-2 text-sm font-bold text-zinc-300 hover:border-white"
                >
                  I&apos;m poor (cancel)
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export const acquireAddon: Addon = {
  id: "acquire-website",
  emoji: "🏦",
  label: "Acquire This Website",
  blurb: "$44B, no due diligence. Your name on the logo, everyone else on the street.",
  run: () => window.dispatchEvent(new Event(OPEN_EVENT)),
  Component: AcquireSite,
};
