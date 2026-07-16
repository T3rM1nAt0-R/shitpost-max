"""Validates a fixed embedded list of JSON/TOML/YAML file contents for syntax errors, cycling through them."""

import json
import tomllib

from harness.shitpost_base import Shitpost

FILES = [
    ("config.json", "json", '{"name": "app", "port": 8080}'),
    ("broken.json", "json", '{"name": "app", "port": 8080'),
    ("pyproject.toml", "toml", 'name = "app"\nport = 8080\n'),
    ("broken.toml", "toml", 'name = "app\nport = 8080\n'),
    ("settings.yaml", "yaml", 'name: app\nport: 8080\n'),
    ("broken.yaml", "yaml", 'name: app\n\tport: 8080\n'),
]


def _validate(kind, content):
    if kind == "json":
        try:
            json.loads(content)
            return True, None
        except json.JSONDecodeError as exc:
            return False, str(exc)
    if kind == "toml":
        try:
            tomllib.loads(content)
            return True, None
        except tomllib.TOMLDecodeError as exc:
            return False, str(exc)
    # yaml: stdlib-only heuristic (no PyYAML dependency available offline) --
    # a tab character in indentation is invalid per the YAML spec.
    for i, line in enumerate(content.splitlines(), start=1):
        if "\t" in line:
            return False, f"line {i}: tab character not allowed in YAML indentation"
    return True, None


class ConfigValidatorPlugin(Shitpost):
    """Emit validation verdict for one FILES entry per tick, cycling through the list."""

    name = "config-validator"
    internal = False
    commit_template = "config-validate {filename}: {is_valid}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        filename, filetype, content = FILES[index]
        is_valid, error = _validate(filetype, content)

        result = {
            "filename": filename,
            "filetype": filetype,
            "is_valid": is_valid,
            "error": error,
        }

        self._save_persisted_state({"index": (index + 1) % len(FILES)})

        return result
