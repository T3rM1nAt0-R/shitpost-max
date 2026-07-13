import json
import os
import random
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost

# SEEDS embedded directly (not read from seeds.txt) to avoid the external-dataset
# ambiguity flagged for anagram-hunter -- same deliberate choice as markov-nonsense.
SEEDS = ["anna", "brian", "carla", "derek", "elena"]

def _env_int(name, default):
    return int(os.environ.get(name, str(default)))



def build_ngram_table(seeds: list, order: int = 2) -> dict:
    table = {}
    for name in seeds:
        padded = name + "\n"
        for i in range(len(padded) - order):
            key = padded[i:i+order]
            next_char = padded[i+order]
            table.setdefault(key, {})
            table[key][next_char] = table[key].get(next_char, 0) + 1
    return table


def generate_name(table: dict, rng, order: int = 2, max_length: int = 12) -> str:
    start_keys = list(table.keys())
    current_key = rng.choice(start_keys)
    name = current_key

    while True:
        if current_key not in table:
            break
        next_char = rng.choices(list(table[current_key].keys()), weights=list(table[current_key].values()), k=1)[0]
        if next_char == "\n":
            break
        name += next_char
        if len(name) >= max_length:
            break

    return name.strip()


class NameGeneratorPlugin(Shitpost):
    """Generate a random name using an n-gram model."""

    name = "name-generator"
    internal = False
    commit_template = "name: {name} (len {length})"

    def __init__(self):
        super().__init__()
        self._state_file_name = "name_generator_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: name generator state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            required = {"tick", "recent_names", "total_generated"}
            if not required.issubset(state.keys()):
                print(
                    "warning: name generator state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "recent_names": [],
            "total_generated": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        chain_order = _env_int("CHAIN_ORDER", 2)
        dedup_window = _env_int("DEDUP_WINDOW", 100)
        max_name_length = _env_int("MAX_NAME_LENGTH", 12)

        table = build_ngram_table(SEEDS, order=chain_order)
        rng = random.Random()

        for _ in range(3):
            name = generate_name(table, rng, order=chain_order, max_length=max_name_length)
            if name not in state["recent_names"]:
                break
        else:
            name = f"{name}_{state['total_generated']}"

        state["recent_names"].append(name)
        if len(state["recent_names"]) > dedup_window:
            state["recent_names"] = state["recent_names"][-dedup_window:]

        state["total_generated"] += 1
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "name": name,
            "length": len(name),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


