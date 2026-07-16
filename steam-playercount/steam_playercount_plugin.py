"""Tracks concurrent players on a chosen Steam game hourly, because someone needs to know if anyone else is still playing."""

import json
import os
from datetime import datetime, timezone
from urllib.request import urlopen

from harness.shitpost_base import Shitpost


class SteamPlayercountPlugin(Shitpost):
    """Fetch concurrent players for a chosen Steam game and log hourly."""

    name = "steam-playercount"
    internal = False
    commit_template = "steam-playercount: {game_name} {players} players"

    def __init__(self):
        super().__init__()
        self._app_id = os.getenv("APP_ID", "730")
        self._api_key = os.getenv("STEAM_API_KEY")
        self._game_name = os.getenv("GAME_NAME", "CS:GO")

    def produce(self) -> dict:
        """Fetch player count and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(default={"app_id": "730", "game_name": "CS:GO", "players": 0, "timestamp": None})

        # Fetch the current player count.
        players = self._fetch_player_count()

        # Update the state with new data.
        state["app_id"] = self._app_id
        state["game_name"] = self._game_name
        state["players"] = players
        state["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._save_persisted_state(state)

        return {
            "tick": 1,
            "app_id": self._app_id,
            "game_name": self._game_name,
            "players": players,
            "timestamp": state["timestamp"],
        }

    def _fetch_player_count(self) -> int:
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={self._app_id}&key={self._api_key}"
        response = urlopen(url)
        data = json.loads(response.read().decode("utf-8"))
        return data["response"]["player_count"]
