"""Tallies recurring subscription costs monthly, so I can be quietly horrified on a schedule."""

import hashlib
import json
import os
import sys
import yaml
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class SubscriptionAuditPlugin(Shitpost):
    """Log recurring subscription costs and tally the monthly total."""

    name = "subscription-audit"
    internal = False
    commit_template = "subscriptions: {monthly_total}/mo ({subscriptions_count} items)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"
        self._subscriptions_file_name = "subscriptions.yaml"
        self._last_hash_file_name = "last_hash.txt"
        self._chart_file_name = "chart.svg"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return [json.loads(line.strip()) for line in f]

        return []

    def _save_state(self, plugin_dir: str, state: list) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        with open(path, "w", encoding="utf-8") as f:
            for entry in state:
                f.write(json.dumps(entry) + "\n")

    @staticmethod
    def _default_subscriptions() -> list:
        """Return sensible default subscriptions for first-run auto-creation."""
        return [
            {"name": "Netflix Standard", "amount": 15.49, "frequency": "monthly"},
            {"name": "Spotify Premium", "amount": 10.99, "frequency": "monthly"},
            {"name": "iCloud+ 200GB", "amount": 2.99, "frequency": "monthly"},
            {"name": "Amazon Prime", "amount": 139.00, "frequency": "yearly"},
        ]

    def _load_subscriptions(self, plugin_dir: str) -> list:
        """Load the subscription list."""
        path = os.path.join(plugin_dir, self._subscriptions_file_name)
        if not os.path.exists(path):
            self._create_default_subscriptions(path)

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _create_default_subscriptions(self, path: str) -> None:
        """Create subscriptions.yaml with sensible defaults if missing."""
        defaults = self._default_subscriptions()
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(defaults, f, default_flow_style=False)
        print(f"[{self.name}] Created default {os.path.basename(path)} ({len(defaults)} entries)", file=sys.stderr)

    def _save_subscriptions_hash(self, plugin_dir: str, hash_value: str) -> None:
        """Save the hash of subscriptions.yaml."""
        path = os.path.join(plugin_dir, self._last_hash_file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(hash_value)

    def _load_subscriptions_hash(self, plugin_dir: str) -> str:
        """Load the hash of subscriptions.yaml."""
        path = os.path.join(plugin_dir, self._last_hash_file_name)
        if not os.path.exists(path):
            return ""

        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def _compute_monthly_total(self, subscriptions: list) -> float:
        """Compute the monthly total for given subscriptions."""
        currency = os.getenv("CURRENCY", "USD")
        monthly_total = 0.0
        for sub in subscriptions:
            amount = sub["amount"]
            frequency = sub["frequency"].lower()
            if frequency == "monthly":
                monthly_total += amount
            elif frequency == "yearly":
                monthly_total += amount / 12
            else:
                raise ValueError(f"Unsupported frequency: {frequency}")

        return monthly_total

    def produce(self) -> dict | None:
        """Return the subscription audit tick or skip if unchanged."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        # Ensure subscriptions.yaml exists (auto-create defaults if missing).
        self._load_subscriptions(plugin_dir)

        current_hash = hashlib.sha256(open(os.path.join(plugin_dir, self._subscriptions_file_name), "rb").read()).hexdigest()
        last_hash = self._load_subscriptions_hash(plugin_dir)

        if current_hash == last_hash:
            return None

        subscriptions = self._load_subscriptions(plugin_dir)
        monthly_total = self._compute_monthly_total(subscriptions)
        yearly_total = monthly_total * 12
        subscriptions_count = len(subscriptions)

        state_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monthly_total": monthly_total,
            "yearly_total": yearly_total,
            "subscriptions_count": subscriptions_count,
        }

        self._save_state(plugin_dir, [state_entry])
        self._save_subscriptions_hash(plugin_dir, current_hash)

        return state_entry
