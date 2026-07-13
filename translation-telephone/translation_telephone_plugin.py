import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class TranslationTelephonePlugin(Shitpost):
    """Translate a sentence through 5 language hops and back to English."""

    name = "translation-telephone"
    internal = False
    commit_template = "telephone: {original_truncated} → {final_truncated}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "translation_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running translation state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: translation state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "original", "chain"}
            if not required.issubset(state.keys()):
                print(
                    "warning: translation state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "original": "",
            "chain": {}
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        # Placeholder for actual translation logic using Ollama
        return f"Translated from {src_lang} to {tgt_lang}: {text}"

    def produce(self) -> dict:
        """Run the 5-hop translation chain and compute drift."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        if not state["original"]:
            # Set a default original sentence for demonstration
            state["original"] = "Hello, world!"
            state["tick"] += 1

        chain = {}
        current_text = state["original"]

        for i in range(5):
            src_lang = ["en", "es", "fr", "de", "it"][i]
            tgt_lang = ["es", "fr", "de", "it", "en"][i]
            translated_text = self._translate(current_text, src_lang, tgt_lang)
            chain[src_lang] = translated_text
            current_text = translated_text

        final_text = chain["en"]
        similarity = self._compute_similarity(state["original"], final_text)

        state["chain"] = chain
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "original": state["original"],
            "original_truncated": state["original"][:40],
            "chain": chain,
            "final_truncated": final_text[:40],
            "similarity": similarity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute character n-gram overlap similarity."""
        trigrams1 = set(text1[i:i+3] for i in range(len(text1)-2))
        trigrams2 = set(text2[i:i+3] for i in range(len(text2)-2))
        return len(trigrams1.intersection(trigrams2)) / min(len(trigrams1), len(trigrams2))
