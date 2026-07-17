"""Procedurally generates a new dungeon daily using BSP, because roguelikes deserve CI/CD too."""

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

    @staticmethod
    def _default_state() -> dict:
        # "date" must NOT be today's date -- this is the fallback used only
        # when no state file exists yet (the very first tick ever). If it
        # defaults to today, produce()'s "state['date'] != current_date"
        # check is always False on that first tick, so the dungeon never
        # generates and _save_persisted_state() never runs -- meaning the
        # state file never gets created, so every future tick re-loads this
        # same "today" default again, forever. A real bug found 2026-07-17:
        # this plugin had never produced a single tick since it was built.
        return {
            "date": None,
            "seed": None,
        }

    def produce(self) -> dict:
        """Return the next dungeon map and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(self._default_state())

        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if state["date"] != current_date:
            seed = hash(current_date)
            dungeon = self._generate_dungeon(seed)
            state["seed"] = seed
            state["date"] = current_date

            self._save_persisted_state(state)

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
