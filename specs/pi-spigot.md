# pi-spigot

**One-line:** Each tick emits the next decimal digit of π, using an integer-only streaming spigot algorithm.

**Difficulty:** 🟡 *real*

**What it secretly teaches:** streaming algorithms, arbitrary-precision integer arithmetic, and the discipline of maintaining state across ticks instead of recomputing from scratch.

**Output per tick:** One digit appended to `pi_digits.txt`. Over time the file becomes a never-ending decimal expansion of π, one commit at a time.

**Algorithm:** Use Jeremy Gibbons' *Unbounded Spigot Algorithm* (or an equivalent integer-only decimal spigot). It maintains a small matrix/ziplist of integers and produces one decimal digit per tick without floating-point math. The classic BBP formula gives hex digits; this stays decimal so each commit is readable.

**Tick cadence:** Configurable via `TICK_SECONDS` env var (default 60). The goal is regular, not fast.

**State file:** `pi_digits.txt` — plain text, one continuous digit stream. Optionally also write a `pi_log.jsonl` with metadata: `{tick, digit, total_digits_seen, timestamp}`.

**Commit message convention:** `pi: digit 1234 = 5` or similar.

**Extensions:**
- Emit a block of N digits per commit instead of one.
- Add a tiny `README.md` badge that shows current digit count.
- Plot the digit distribution (0–9) as a second file.
- Compare the stream against a known-good π source for regression testing.

**Why this is a good first repo:** It is a classic "looks easy, has real CS inside" example. The spigot algorithm is short but non-obvious, and the output is instantly satisfying.
