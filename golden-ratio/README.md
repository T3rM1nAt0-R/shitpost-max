# golden-ratio

A shitpost-max plugin that emits one decimal digit of the golden ratio φ per tick.

## Algorithm

φ has the simplest continued-fraction expansion,

```
φ = [1; 1, 1, 1, ...]
```

so its convergents are consecutive Fibonacci ratios F_{n+1}/F_n.  The
recurrence is

```
p_{-1} = 1, p_0 = 1, q_{-1} = 0, q_0 = 1
p_n = p_{n-1} + p_{n-2}
q_n = q_{n-1} + q_{n-2}
```

Each tick advances the recurrence at least once and compares two successive
convergents.  The next unclaimed decimal digit is emitted only when both
convergents agree on it, guaranteeing that every emitted digit is stable.

## Digit numbering

`phi_digits.txt` stores the decimal expansion as a continuous string of digits
**including the leading integer digit**.  So the first few entries are:

```
φ = 1.6180339887...
phi_digits.txt -> "16180339887..."
```

`total_digits_seen` counts from that leading `1` as digit 1.

## Files

- `phi_spigot.py` — plugin implementation.
- `tick.py` — cron entry point; calls `PhiSpigotPlugin().run_tick()`.
- `phi_digits.txt` — accumulated digits of φ.
- `spigot_state.json` — running convergent state.
- `state.jsonl` — one JSON line per tick (written by the harness).
- `summary.json` — latest tick summary (written by the harness).

## Environment variables

- `TICK_SECONDS` — target cadence between ticks (default: `60`).  Used by the
  external scheduler/cron that invokes `tick.py`.
- `BATCH_SIZE` — digits to emit per invocation (default: `1`).  The plugin
  emits exactly one stable digit per `produce()` call.

## Commit message

```
φ: digit {total_digits_seen} = {digit} (convergent {convergent_n})
```
