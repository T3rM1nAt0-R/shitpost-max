"""Prompts the LLM to extract structured fields from unstructured text as JSON and measures accuracy."""

import re

import json
import urllib.request

OLLAMA_URL = "http://localhost:1601/api/generate"
MODEL = "qwen2.5-coder:7b-instruct-q6_K"


def _call_ollama(prompt, num_predict=None):
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    if num_predict is not None:
        payload["options"] = {"num_predict": num_predict}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read())
    return result["response"].strip()

from harness.shitpost_base import Shitpost

SNIPPETS = [
    (
        "Invoice #4471 dated 2026-03-14 for a total of $250.00 was sent to the client.",
        {"date": "2026-03-14", "amount": "250.00"},
    ),
    (
        "On July 4th, 2025, Maria paid $89.99 for the annual subscription.",
        {"date": "July 4th, 2025", "amount": "89.99"},
    ),
    (
        "The meeting on 2026-01-09 resulted in a budget approval of $12,500.",
        {"date": "2026-01-09", "amount": "12,500"},
    ),
]

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _extract_json(response_text):
    cleaned = _FENCE_RE.sub("", response_text).strip()
    return json.loads(cleaned)


def _score(extracted, expected):
    matches = 0
    for key, expected_value in expected.items():
        actual_value = str(extracted.get(key, "")).strip().lower()
        if actual_value == str(expected_value).strip().lower():
            matches += 1
    return matches / len(expected)


class ExtractionBenchPlugin(Shitpost):
    """Emit an extraction-accuracy result for one SNIPPETS entry per tick, cycling through the list."""

    name = "extraction-bench"
    internal = False
    commit_template = "extraction #{snippet_index}: {accuracy} accuracy"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        text, expected = SNIPPETS[index]
        prompt = (
            "Extract the date and amount from this text as JSON with keys "
            '"date" and "amount". Respond with ONLY the JSON object.\n\n'
            f"Text: {text}"
        )

        try:
            raw = _call_ollama(prompt)
            extracted = _extract_json(raw)
        except Exception:
            return None

        accuracy = _score(extracted, expected)

        result = {
            "snippet_index": index,
            "extracted": extracted,
            "accuracy": round(accuracy, 2),
        }

        self._save_persisted_state({"index": (index + 1) % len(SNIPPETS)})

        return result
