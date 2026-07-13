import json
import os
import sys
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
        self._state_file_name = "steam_playercount_state.json"
        self._app_id = os.getenv("APP_ID", "730")
        self._api_key = os.getenv("STEAM_API_KEY")
        self._game_name = os.getenv("GAME_NAME", "CS:GO")

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: steam-playercount state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"app_id", "game_name", "players", "timestamp"}
            if not required.issubset(state.keys()):
                print(
                    "warning: steam-playercount state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "app_id": "730",
            "game_name": "CS:GO",
            "players": 0,
            "timestamp": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _fetch_player_count(self) -> int:
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={self._app_id}&key={self._api_key}"
        response = urlopen(url)
        data = json.loads(response.read().decode("utf-8"))
        return data["response"]["player_count"]

    def produce(self) -> dict:
        """Fetch player count and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Fetch the current player count.
        players = self._fetch_player_count()

        # Update the state with new data.
        state["app_id"] = self._app_id
        state["game_name"] = self._game_name
        state["players"] = players
        state["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._save_state(plugin_dir, state)

        return {
            "tick": 1,
            "app_id": self._app_id,
            "game_name": self._game_name,
            "players": players,
            "timestamp": state["timestamp"],
        }
