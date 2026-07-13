import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class SpotifyCharts(Shitpost):
    """Daily snapshot of regional Spotify top tracks."""

    name = "spotify-charts"
    internal = False
    commit_template = "spotify-charts: {region} #1 {top_track} - {artist}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "spotify_charts_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: spotify-charts state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"region", "playlist_id", "top_track", "artist", "timestamp"}
            if not required.issubset(state.keys()):
                print(
                    "warning: spotify-charts state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "region": os.getenv("REGION", "India"),
            "playlist_id": os.getenv("PLAYLIST_ID", "37i9dQZEVXbLZ52XmnySJg"),
            "top_track": "",
            "artist": "",
            "timestamp": ""
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Fetch the top track and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Fetch OAuth2 token
        auth_url = "https://accounts.spotify.com/api/token"
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
            "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET")
        }
        response = requests.post(auth_url, data=auth_data)
        if response.status_code != 200:
            print(f"Failed to fetch OAuth2 token: {response.text}", file=sys.stderr)
            return None

        access_token = response.json().get("access_token")
        if not access_token:
            print("No access token received", file=sys.stderr)
            return None

        # Fetch playlist tracks
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        playlist_url = f"https://api.spotify.com/v1/playlists/{state['playlist_id']}/tracks"
        response = requests.get(playlist_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch playlist tracks: {response.text}", file=sys.stderr)
            return None

        tracks = response.json().get("items", [])
        if not tracks:
            print("No tracks found in the playlist", file=sys.stderr)
            return None

        # Parse top track
        top_track = tracks[0].get("track")
        if not top_track:
            print("Top track not found", file=sys.stderr)
            return None

        state["top_track"] = top_track.get("name", "")
        state["artist"] = ", ".join([artist.get("name") for artist in top_track.get("artists", [])])
        state["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._save_state(plugin_dir, state)

        return {
            "region": state["region"],
            "top_track": state["top_track"],
            "artist": state["artist"],
            "timestamp": state["timestamp"]
        }
