"""Estimates token count and cost for fixed sample texts using a chars-per-token heuristic. No network dependency."""

import math

from harness.shitpost_base import Shitpost

TEXTS = [
    "Hello, world!",
    "The quick brown fox jumps over the lazy dog.",
    "def add(a, b):\n    return a + b",
    "Machine learning models require large amounts of training data to perform well.",
    "OK",
]
CHARS_PER_TOKEN = 4
PRICE_PER_1K_TOKENS = 0.002


def _estimate(text):
    tokens = math.ceil(len(text) / CHARS_PER_TOKEN)
    cost = tokens / 1000 * PRICE_PER_1K_TOKENS
    return {"estimated_tokens": tokens, "estimated_cost_usd": cost}


class TokenCounterDemoPlugin(Shitpost):
    """Emit a token/cost estimate for one TEXTS entry per tick, cycling through the list."""

    name = "token-counter-demo"
    internal = False
    commit_template = "tokens: {estimated_tokens} (~${estimated_cost_usd})"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        text = TEXTS[index]
        estimate = _estimate(text)

        result = {
            "text": text,
            "estimated_tokens": estimate["estimated_tokens"],
            "estimated_cost_usd": round(estimate["estimated_cost_usd"], 6),
        }

        self._save_persisted_state({"index": (index + 1) % len(TEXTS)})

        return result
