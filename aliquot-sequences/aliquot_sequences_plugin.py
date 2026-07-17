"""Computes the aliquot sequence for a fixed cycling list of starting integers, capped at 30 steps or 1e8."""

from harness.shitpost_base import Shitpost

STARTS = [12, 6, 220, 25, 95]
MAX_STEPS = 30
VALUE_CAP = 10 ** 8


def _aliquot_sum(n):
    if n <= 1:
        return 0
    total = 1
    i = 2
    while i * i <= n:
        if n % i == 0:
            total += i
            j = n // i
            if j != i:
                total += j
        i += 1
    return total


def _sequence(start):
    sequence = [start]
    seen = {start}
    for _ in range(MAX_STEPS):
        current = sequence[-1]
        if current == 0:
            return sequence, "terminated"
        nxt = _aliquot_sum(current)
        if nxt > VALUE_CAP:
            return sequence, "diverged"
        if nxt in seen:
            sequence.append(nxt)
            return sequence, "cycle"
        sequence.append(nxt)
        seen.add(nxt)
        if nxt == 0:
            return sequence, "terminated"
    return sequence, "max_steps_reached"


class AliquotSequencesPlugin(Shitpost):
    """Emit one starting integer's full aliquot sequence per tick, cycling through STARTS."""

    name = "aliquot-sequences"
    internal = False
    commit_template = "aliquot({start}): {status} after {step_count} steps"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        start = STARTS[index]

        sequence, status = _sequence(start)

        result = {
            "start": start,
            "sequence": sequence,
            "status": status,
            "step_count": len(sequence) - 1,
        }

        self._save_persisted_state({"index": (index + 1) % len(STARTS)})

        return result
