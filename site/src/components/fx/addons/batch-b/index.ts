import type { Addon } from "../types";
import { acquireAddon } from "./acquire";
import { butlerAddon } from "./butler";
import { hotTakesAddon } from "./hotTakes";
import { redactAddon } from "./redact";
import { rocketAddon } from "./rocket";

export const addonsB: Addon[] = [acquireAddon, hotTakesAddon, rocketAddon, butlerAddon, redactAddon];
