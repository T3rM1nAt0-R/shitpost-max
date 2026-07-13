import json
import os
import sys
from datetime import datetime, timezone
import random

from harness.shitpost_base import Shitpost


class FakeChangelogPlugin(Shitpost):
    """Generate a plausible-sounding changelog entry for a product that does not exist."""

    name = "fake-changelog"
    internal = False
    commit_template = "changelog: {product_name} v{version}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "fake_changelog_state.json"
        self._changelog_file_name = "CHANGELOG.md"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running changelog state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: fake-changelog state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "product_name", "version"}
            if not required.issubset(state.keys()):
                print(
                    "warning: fake-changelog state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "product_name": "",
            "version": ""
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_changelog(self, plugin_dir: str, product_name: str, version: str, changelog_text: str) -> None:
        path = os.path.join(plugin_dir, self._changelog_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(changelog_text + "\n")

    def produce(self) -> dict:
        """Return a fake changelog entry and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Generate a new product name and version
        product_name = f"Product{random.randint(100, 999)}"
        version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

        # Generate a fake changelog entry
        changelog_text = self._generate_changelog(product_name, version)

        # Append the changelog to the file
        self._append_changelog(plugin_dir, product_name, version, changelog_text)

        # Update state
        state["tick"] += 1
        state["product_name"] = product_name
        state["version"] = version

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "product_name": product_name,
            "version": version,
            "changelog_text_length_chars": len(changelog_text),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_changelog(self, product_name: str, version: str) -> str:
        changelog_template = f"""
## {product_name} v{version}

### Added
- Feature A

### Fixed
- Bug B

### Changed
- Refactor C
"""

        return changelog_template
