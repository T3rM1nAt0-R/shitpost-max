import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from perfect_plugin import PerfectNumbersPlugin


KNOWN_MERSENNE_PRIME_EXPONENTS = [2, 3, 5, 7, 13, 17, 19]
KNOWN_NON_MERSENNE_PRIME_EXPONENTS = [11, 23, 29]
KNOWN_PERFECT_NUMBERS = {2: 6, 3: 28, 5: 496, 7: 8128, 13: 33550336, 17: 8589869056, 19: 137438691328, 31: 2305843008139952128, 61: 2658455991569831744654692615953842176}


def test_is_prime():
    plugin = PerfectNumbersPlugin()
    for n in [2, 3, 5, 7, 11, 13, 17, 19, 23]:
        assert plugin._is_prime(n) is True
    for n in [1, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20]:
        assert plugin._is_prime(n) is False


def test_next_prime():
    plugin = PerfectNumbersPlugin()
    assert plugin._next_prime(1) == 2
    assert plugin._next_prime(2) == 3
    assert plugin._next_prime(3) == 5
    assert plugin._next_prime(5) == 7
    assert plugin._next_prime(7) == 11
    assert plugin._next_prime(11) == 13


def test_lucas_lehmer_known_mersenne_primes():
    plugin = PerfectNumbersPlugin()
    for p in KNOWN_MERSENNE_PRIME_EXPONENTS:
        assert plugin._lucas_lehmer(p) is True, f"p={p} should be a Mersenne prime exponent"


def test_lucas_lehmer_known_non_mersenne_primes():
    plugin = PerfectNumbersPlugin()
    for p in KNOWN_NON_MERSENNE_PRIME_EXPONENTS:
        assert plugin._lucas_lehmer(p) is False, f"p={p} should NOT be a Mersenne prime exponent"


def test_produce_sequence_matches_known_perfect_numbers(tmp_path, monkeypatch):
    plugin = PerfectNumbersPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    found = {}
    for _ in range(20):
        result = plugin.produce()
        if result is not None:
            found[result["p"]] = result["perfect_number"]

    assert found == KNOWN_PERFECT_NUMBERS
