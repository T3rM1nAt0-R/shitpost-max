"""Generates a plausible changelog entry for a product that does not exist, more convincing than most real ones."""

import os
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
        self._changelog_file_name = "CHANGELOG.md"

    def _append_changelog(self, plugin_dir: str, product_name: str, version: str, changelog_text: str) -> None:
        path = os.path.join(plugin_dir, self._changelog_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(changelog_text + "\n")

    def produce(self) -> dict:
        """Return a fake changelog entry and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"tick": 0, "product_name": "", "version": ""})

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

        self._save_persisted_state(state)

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
