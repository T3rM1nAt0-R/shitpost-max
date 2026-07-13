import json
import os
import sys
from datetime import datetime, timezone
import requests
import numpy as np
from nltk import word_tokenize
from nltk.corpus import stopwords

from harness.shitpost_base import Shitpost


class TemperatureLabPlugin(Shitpost):
    """Run prompts at different temperatures and log output variance."""

    name = "temperature-lab"
    internal = False
    commit_template = "temperature-lab: σ={length_stddev}, T0={temp_0_0_length}c, T2={temp_2_0_length}c"

    def __init__(self):
        super().__init__()
        self._state_file_name = "temperature_lab_state.json"
        self._output_dir = os.path.join(self._plugin_dir(), "outputs")
        os.makedirs(self._output_dir, exist_ok=True)

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "prompts": [
                {"id": "poem", "prompt": "Write a poem about the moon."},
                {"id": "story", "prompt": "Tell me a story about a dragon."},
                {"id": "dialogue", "prompt": "Conduct a conversation between two characters."},
                {"id": "idea", "prompt": "What's an interesting idea for a new product?"},
                {"id": "question", "prompt": "What is the meaning of life, the universe, and everything?"}
            ],
            "temperatures": [0.0, 0.3, 0.7, 1.0, 1.5, 2.0],
            "max_tokens": 512
        }

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at default."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: temperature-lab state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "prompts", "temperatures", "max_tokens"}
            if not required.issubset(state.keys()):
                print(
                    "warning: temperature-lab state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _send_prompt(self, prompt: str, temperature: float) -> str:
        model = os.getenv("MODEL", "qwen2.5:7b")
        endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
        max_tokens = int(os.getenv("MAX_TOKENS", 512))

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            return response.json().get("output", "")
        else:
            print(f"Error sending prompt: {response.text}", file=sys.stderr)
            return ""

    def _compute_metrics(self, outputs: list) -> dict:
        lengths = [len(output) for output in outputs]
        ttr = self._type_token_ratio(outputs)

        return {
            "length_stddev": np.std(lengths),
            "temp_0_0_length": lengths[0],
            "temp_2_0_length": lengths[-1],
            "ttr": ttr
        }

    @staticmethod
    def _type_token_ratio(texts: list) -> float:
        words = [word_tokenize(text.lower()) for text in texts]
        stop_words = set(stopwords.words('english'))
        filtered_words = [[word for word in sentence if word.isalnum() and word not in stop_words] for sentence in words]
        unique_words = set(word for sentence in filtered_words for word in sentence)
        return len(unique_words) / sum(len(sentence) for sentence in filtered_words)

    def produce(self) -> dict:
        """Run prompts at different temperatures and log output variance."""
        plugin_dir = self._plugin_dir()
        state = self._load_state(plugin_dir)

        tick = state["tick"] + 1
        results = []

        for prompt in state["prompts"]:
            prompt_id = prompt["id"]
            prompt_text = prompt["prompt"]

            outputs = [self._send_prompt(prompt_text, temp) for temp in state["temperatures"]]
            metrics = self._compute_metrics(outputs)

            for i, output in enumerate(outputs):
                length = len(output)
                filename = os.path.join(self._output_dir, f"{tick}_{prompt_id}_temp{state['temperatures'][i]}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(output)

                results.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "prompt_id": prompt_id,
                    "temperature": state["temperatures"][i],
                    "output": output,
                    "length": length,
                    "ttr": metrics["ttr"]
                })

        state["tick"] = tick
        self._save_state(plugin_dir, state)

        return {
            "tick": tick,
            "results": results,
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
