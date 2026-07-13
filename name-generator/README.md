# name-generator

Character-level Markov chain name generator. See `atlas-docs/mind-junkyard/shitpost-max/name-generator/` for the full spec.

**Two deliberate deviations from design.md**, found via DeepSeek review 2026-07-13:
- `SEEDS` is embedded directly rather than read from `seeds.txt` — avoids the external-dataset-sourcing ambiguity flagged for `anagram-hunter`, same choice as `markov-nonsense`.
- No separate `name_log.jsonl`/`name_stats.json` — the shared harness (`Shitpost` base class) already writes `state.jsonl`/`summary.json` automatically from `produce()`'s return value; design.md predates that convention.

`CHAIN_ORDER`, `DEDUP_WINDOW`, `MAX_NAME_LENGTH` are read from env with the spec's defaults.
