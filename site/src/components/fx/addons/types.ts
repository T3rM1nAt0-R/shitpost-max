import type { ComponentType } from "react";

/**
 * One absurd add-on. `run` fires from the Billionaire Control Panel; `Component`
 * (optional) is mounted once for the whole site and must stay idle-cheap: no
 * permanent requestAnimationFrame loops, no blur/backdrop filters, no blend modes,
 * animate only transform/opacity, and respect prefers-reduced-motion.
 */
export interface Addon {
  id: string;
  emoji: string;
  label: string;
  /** One-line billionaire-voice description shown under the button. */
  blurb: string;
  run?: () => void;
  Component?: ComponentType;
}

/** Fire-and-forget event bus so add-ons can be triggered by id from anywhere. */
export const ADDON_EVENT = "spm-addon";
export function triggerAddon(id: string) {
  window.dispatchEvent(new CustomEvent(ADDON_EVENT, { detail: id }));
}
