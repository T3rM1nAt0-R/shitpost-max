# word-of-the-day

Random word + optional Ollama-generated example sentence per tick, with a template fallback. See `atlas-docs/mind-junkyard/shitpost-max/word-of-the-day/` for the full spec.

**Deliberate deviation from design.md**: `WORDLIST` is embedded directly (5 entries) rather than read from an external `wordlist.json` (500 entries) — same external-dataset-ambiguity avoidance as `markov-nonsense`/`name-generator`.
