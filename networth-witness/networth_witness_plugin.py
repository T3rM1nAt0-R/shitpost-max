"""Computes an absolutely real net worth, denominated in ShitCoin (SC), under the 100,000,000x Engineering Valuation Model. Your commits are worth 100,000,000 SC each, obviously."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost

FAKE_NET_WORTH_MULTIPLIER = 100_000_000


def _commit_count(repo_root):
    """Return the total number of commits reachable from HEAD, or None on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=repo_root,
        )
    except (subprocess.TimeoutExpired, OSError):
        # DeepSeek review, 2026-07-17: catching only TimeoutExpired let
        # FileNotFoundError (git not on PATH), PermissionError, and other
        # OSError subclasses escape uncaught, violating design.md's "None
        # on any failure" contract for this function.
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


class NetWorthWitnessPlugin(Shitpost):
    """Compute a fake net worth (in ShitCoin) from this repo's own commit count and chart it over time.

    Redesigned 2026-07-17: the original manual-entry design (a real `NETWORTH` env var) never
    produced a single tick, since it was never configured -- and fabricating a real financial
    figure on someone's behalf isn't this plugin's job. Now fully automatic: no input, no real
    money, just commits times a very large made-up number, denominated in an invented currency.
    """

    name = "networth-witness"
    internal = False
    commit_template = "networth: {net_worth_sc:,} SC ({commit_count:,} commits x 100,000,000 SC/commit)"

    def __init__(self):
        super().__init__()
        # Real bug, found 2026-07-17: "state.jsonl" is the exact filename
        # the harness's own _append_state() writes to automatically --
        # this plugin's own _save_state() truncate-rewrites that same file
        # every tick, colliding with the harness's log. Renamed to a
        # distinct filename so the two never collide.
        self._state_file_name = "networth_witness_history.jsonl"

    def _load_state(self, plugin_dir: str) -> list:
        """Load the running net-worth history, or initialise it as an empty list."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: networth state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
            required = {"timestamp", "commit_count", "net_worth_sc"}
            if not all(required.issubset(item.keys()) for item in state):
                print(
                    "warning: networth state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return []
            return state

        return []

    def _save_state(self, plugin_dir: str, state: list) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for item in state:
                json.dump(item, f)
                f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Return the next fake net-worth entry and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)
        repo_root = os.path.dirname(plugin_dir)

        commit_count = _commit_count(repo_root)
        if commit_count is None:
            print("warning: could not determine commit count; skipping tick", file=sys.stderr)
            return None

        net_worth_sc = commit_count * FAKE_NET_WORTH_MULTIPLIER
        timestamp = datetime.now(timezone.utc).isoformat()

        state = self._load_state(plugin_dir)
        state.append({"timestamp": timestamp, "commit_count": commit_count, "net_worth_sc": net_worth_sc})
        self._save_state(plugin_dir, state)

        return {
            "commit_count": commit_count,
            "net_worth_sc": net_worth_sc,
            "entry_count": len(state),
            "timestamp": timestamp,
        }
