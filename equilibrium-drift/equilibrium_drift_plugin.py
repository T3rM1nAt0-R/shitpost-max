"""Disrupted the multi-trillion-dollar market-equilibrium prediction space with a blockchain-verified random-walk return-to-parity engine. 10,000,000x engineering, powered by a random walk nobody asked to be disrupted."""

from harness.shitpost_base import Shitpost

A = 1103515245
C = 12345
M = 2 ** 31
SEED = 42
CAP = 100000
WINDOW_SIZE = 200


def _lcg_next(state):
    new_state = (A * state + C) % M
    return new_state, new_state / M


def _first_return_time(lcg_state, cap):
    position = 0
    for toss in range(1, cap + 1):
        lcg_state, u = _lcg_next(lcg_state)
        position += 1 if u < 0.5 else -1
        if position == 0:
            return lcg_state, toss, False
    return lcg_state, cap, True


def _update_running_mean(count, running_sum, new_value):
    new_count = count + 1
    new_sum = running_sum + new_value
    return new_count, new_sum, new_sum / new_count


def _windowed_median(window):
    sw = sorted(window)
    n = len(sw)
    if n % 2 == 1:
        return sw[n // 2]
    return (sw[n // 2 - 1] + sw[n // 2]) / 2


class EquilibriumDriftPlugin(Shitpost):
    """Run one coin-toss-parity-return trial per tick, tracking a running mean vs. windowed median."""

    name = "equilibrium-drift"
    internal = False
    commit_template = "equilibrium-drift trial {trial_index}: {return_time} tosses (mean {running_mean}, median {windowed_median})"

    def produce(self):
        state = self._load_persisted_state({
            "lcg_state": SEED,
            "trial_count": 0,
            "running_sum": 0,
            "window": [],
        })

        new_lcg_state, return_time, capped = _first_return_time(state["lcg_state"], CAP)
        new_count, new_sum, mean = _update_running_mean(
            state["trial_count"], state["running_sum"], return_time
        )

        window = state["window"] + [return_time]
        if len(window) > WINDOW_SIZE:
            window = window[-WINDOW_SIZE:]
        median = _windowed_median(window)

        self._save_persisted_state({
            "lcg_state": new_lcg_state,
            "trial_count": new_count,
            "running_sum": new_sum,
            "window": window,
        })

        return {
            "trial_index": new_count,
            "return_time": return_time,
            "capped": capped,
            "running_trial_count": new_count,
            "running_mean": round(mean, 4),
            "windowed_median": median,
        }
