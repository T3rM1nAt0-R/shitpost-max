# card-shuffler

Shuffles a 52-card deck with 3 algorithms (Fisher-Yates, overhand, naive swap), tracks Shannon entropy over a sliding window. See `atlas-docs/mind-junkyard/shitpost-max/card-shuffler/` for the full spec.

**Deliberate deviations** (documented, not "fixed" against spec): single consolidated plugin file rather than `deck.py`/`algorithms.py`/`entropy.py` (repo CI convention); shuffle functions return a new list rather than mutating in place (safer, avoids corrupting the shared `DECK` constant, and simpler to test).
