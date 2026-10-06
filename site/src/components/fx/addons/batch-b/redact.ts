import type { Addon } from "../types";
import { stamp } from "./sound";
import { toast } from "./util";

const CLASS = "fxb-redacted";

function toggleRedaction() {
  stamp();
  const on = document.documentElement.classList.toggle(CLASS);
  toast({
    title: on ? "⬛ CLASSIFIED" : "📂 DECLASSIFIED",
    text: on
      ? "Effective tax rate: 0.00%. Every number on this page is now a matter of national security."
      : "Numbers restored. The IRS has been notified. Don't worry, they report to me now.",
    ms: 4200,
    slot: "redact",
  });
}

export const redactAddon: Addon = {
  id: "redact-my-taxes",
  emoji: "⬛",
  label: "Redact My Taxes",
  blurb: "What numbers? I don't see any numbers. Neither does the IRS.",
  run: toggleRedaction,
};
