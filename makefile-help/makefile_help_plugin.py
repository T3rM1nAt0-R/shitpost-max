"""Parses a fixed embedded Makefile for target: ## description comments, cycling through a help menu."""

import re

from harness.shitpost_base import Shitpost

MAKEFILE = (
    ".PHONY: build test clean\n\n"
    "build: ## Build the project\n\tgo build -o bin/app\n\n"
    "test: ## Run the test suite\n\tgo test ./...\n\n"
    "clean: ## Remove build artifacts\n\trm -rf bin/\n"
)

_TARGET_RE = re.compile(r"^([a-zA-Z0-9_-]+):.*?##\s*(.+)$", re.MULTILINE)


def _parse_targets(content):
    return [(m.group(1), m.group(2)) for m in _TARGET_RE.finditer(content)]


class MakefileHelpPlugin(Shitpost):
    """Emit one parsed Makefile target per tick, cycling through the list."""

    name = "makefile-help"
    internal = False
    commit_template = "make help {target}: {description}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        targets = _parse_targets(MAKEFILE)
        target, description = targets[index]

        result = {
            "target": target,
            "description": description,
        }

        self._save_persisted_state({"index": (index + 1) % len(targets)})

        return result
