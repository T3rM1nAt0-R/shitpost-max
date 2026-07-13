import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class DungeonOfTheDayPlugin(Shitpost):
    """Generate one procedural dungeon map per day using a BSP algorithm."""

    name = "dungeon-of-the-day"
    internal = False
    commit_template = "dungeon: {date} — {room_count} rooms, {width}x{height}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "dungeon_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running dungeon state, or initialise it at the current date."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: dungeon state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"date", "seed"}
            if not required.issubset(state.keys()):
                print(
                    "warning: dungeon state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "seed": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _generate_dungeon(self, seed: int) -> dict:
        # Placeholder for BSP or random-walk algorithm
        # This is a dummy implementation that returns a fixed dungeon layout
        return {
            "seed": seed,
            "width": 40,
            "height": 25,
            "rooms": [
                {"x": 1, "y": 1, "w": 10, "h": 10},
                {"x": 20, "y": 1, "w": 10, "h": 10},
                {"x": 35, "y": 1, "w": 5, "h": 10}
            ],
            "tiles": [
                [0] * 40 for _ in range(25)
            ]
        }

    def produce(self) -> dict:
        """Return the next dungeon map and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if state["date"] != current_date:
            seed = hash(current_date)
            dungeon = self._generate_dungeon(seed)
            state["seed"] = seed
            state["date"] = current_date

            self._save_state(plugin_dir, state)

            return {
                "date": current_date,
                "seed": seed,
                "width": dungeon["width"],
                "height": dungeon["height"],
                "room_count": len(dungeon["rooms"]),
                "connected": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        return None
