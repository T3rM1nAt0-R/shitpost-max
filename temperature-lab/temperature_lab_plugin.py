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
        self._output_dir = os.path.join(self._plugin_dir(), "outputs")
        os.makedirs(self._output_dir, exist_ok=True)

    def _send_prompt(self, prompt: str, temperature: float) -> str:
        model = os.getenv("MODEL", "qwen2.5-coder:7b-instruct-q6_K")
        endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:1601/api/generate")
        max_tokens = int(os.getenv("MAX_TOKENS", 512))

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "")
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
        state = self._load_persisted_state({
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
        })

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
        self._save_persisted_state(state)

        return {
            "tick": tick,
            "results": results,
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
