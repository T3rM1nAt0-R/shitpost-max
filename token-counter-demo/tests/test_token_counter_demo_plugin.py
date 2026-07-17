import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from token_counter_demo_plugin import _estimate

EXPECTED = [
    ("Hello, world!", 4, 0.000008),
    ("The quick brown fox jumps over the lazy dog.", 11, 0.000022),
    ("def add(a, b):\n    return a + b", 8, 0.000016),
    ("Machine learning models require large amounts of training data to perform well.", 20, 0.00004),
    ("OK", 1, 0.000002),
]


def test_estimate_matches_ground_truth():
    for text, expected_tokens, expected_cost in EXPECTED:
        result = _estimate(text)
        assert result["estimated_tokens"] == expected_tokens
        assert round(result["estimated_cost_usd"], 6) == expected_cost
