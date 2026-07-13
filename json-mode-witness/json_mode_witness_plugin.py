import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class JsonModeWitnessPlugin(Shitpost):
    """Measure JSON compliance of local LLM responses."""

    name = "json-mode-witness"
    internal = False
    commit_template = "json-mode-witness: {valid_count}/{total_combos} valid — best: {best_style} ({best_style_rate:.0%})"

    def __init__(self):
        super().__init__()
        self._state_file_name = "json_mode_witness_state.json"
        self._schemas_file_name = "schemas.json"
        self._styles_file_name = "styles.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: json_mode_witness state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"valid_count", "total_combos", "best_style", "best_style_rate"}
            if not required.issubset(state.keys()):
                print(
                    "warning: json_mode_witness state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "valid_count": 0,
            "total_combos": 0,
            "best_style": None,
            "best_style_rate": 0.0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _load_schemas(self, plugin_dir: str) -> list:
        """Load the prompt/schema pairs."""
        path = os.path.join(plugin_dir, self._schemas_file_name)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_styles(self, plugin_dir: str) -> list:
        """Load the prompting styles."""
        path = os.path.join(plugin_dir, self._styles_file_name)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _validate_response(self, response: str, schema: dict) -> tuple:
        """Validate the response against the schema."""
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            return False, "parse_error", None

        if not isinstance(parsed, dict):
            return False, "schema_mismatch", None

        for key, value in schema["properties"].items():
            if key not in parsed:
                return False, "schema_mismatch", None
            if value["type"] == "string" and not isinstance(parsed[key], str):
                return False, "schema_mismatch", None
            elif value["type"] == "number" and not isinstance(parsed[key], (int, float)):
                return False, "schema_mismatch", None
            elif value["type"] == "array" and not isinstance(parsed[key], list):
                return False, "schema_mismatch", None
            elif value["type"] == "object" and not isinstance(parsed[key], dict):
                return False, "schema_mismatch", None

        return True, "valid", parsed

    def produce(self) -> dict:
        """Run all combinations of schemas and styles, validate responses."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        schemas = self._load_schemas(plugin_dir)
        styles = self._load_styles(plugin_dir)

        valid_count = 0
        total_combos = len(schemas) * len(styles)

        for schema in schemas:
            for style in styles:
                system_prompt_template = style["system_prompt_template"]
                user_prompt_suffix = style["user_prompt_suffix"]

                # Construct the prompt using the style's template.
                prompt = f"{system_prompt_template}\n{schema['prompt']}{user_prompt_suffix}"

                # Send to the model and capture raw output (simulated here).
                response = self._send_to_llm(prompt)

                # Validate the response.
                is_valid, verdict, parsed = self._validate_response(response, schema)

                if is_valid:
                    valid_count += 1

                # Log per-combination results.
                with open(os.path.join(plugin_dir, "state.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "schema_id": schema["id"],
                        "style": style["id"],
                        "raw": response,
                        "parsed": parsed,
                        "verdict": verdict,
                        "error": None if is_valid else response
                    }) + "\n")

        # Update the best-performing style and overall compliance.
        best_style_rate = valid_count / total_combos
        if state["best_style"] is None or best_style_rate > state["best_style_rate"]:
            state["best_style"] = "best_style"
            state["best_style_rate"] = best_style_rate

        state["valid_count"] = valid_count
        state["total_combos"] = total_combos

        self._save_state(plugin_dir, state)

        return {
            "tick": len(state["state.jsonl"]),
            "valid_count": valid_count,
            "total_combos": total_combos,
            "best_style": state["best_style"],
            "best_style_rate": best_style_rate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _send_to_llm(self, prompt: str) -> str:
        """Simulate sending the prompt to the LLM and capturing the response."""
        # Replace this with actual LLM interaction code.
        return '{"languages": [{"name": "Python", "year_created": 1991, "paradigm": "multi-paradigm"}]}'
