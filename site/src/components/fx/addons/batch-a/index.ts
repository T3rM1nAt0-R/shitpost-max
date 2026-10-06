import type { Addon } from "../types";
import { fireEveryoneAddon } from "./fireEveryone";
import { goldenParachuteAddon } from "./goldenParachute";
import { ipoBellAddon } from "./ipoBell";
import { netWorthHudAddon } from "./netWorthHud";
import { trickleDownAddon } from "./trickleDown";

export const addonsA: Addon[] = [
  netWorthHudAddon,
  ipoBellAddon,
  fireEveryoneAddon,
  trickleDownAddon,
  goldenParachuteAddon,
];
