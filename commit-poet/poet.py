"""Writes one line of an infinite poem per tick via LLM. e. e. cummings would've automated it too, probably.

Each tick reads the most recent lines from ``poem.txt``, asks a local Ollama
instance to continue the poem, and appends the new line to ``poem.txt``.  The
same line is returned to the harness as the commit message.

If Ollama is unreachable, times out, or returns an empty response, a hardcoded
fallback line is used so the poem always advances.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


# Placeholder line used when the local LLM cannot be reached or returns nothing.
_FALLBACK_LINE = "[the poet is silent today]"

# Default Ollama request timeout in seconds.  A generous ceiling is used because
# the very first call may need to load the model into memory.
_DEFAULT_TIMEOUT_SECONDS = 120.0

# Markdown-ish wrappers that instruction-tuned models sometimes emit despite
# being told not to.  Used by ``_sanitize_response`` to clean a generated line.
_NUMBERED_PREFIX_RE = re.compile(r"^\d+[.)]\s*")
_WRAPPER_CHARS = {'"', "'", "`"}


def _strip_markdown_wrappers(line: str) -> str:
    """Remove common list/block prefixes and matching quote/backtick wraps."""
    for prefix in ("> ", "- ", "* "):
        if line.startswith(prefix):
            line = line[len(prefix):]
            break
    else:
        match = _NUMBERED_PREFIX_RE.match(line)
        if match:
            line = line[match.end():]

    if len(line) >= 2 and line[0] == line[-1] and line[0] in _WRAPPER_CHARS:
        line = line[1:-1]

    return line.strip()


class CommitPoetPlugin(Shitpost):
    """Generate one line of an infinite poem per tick."""

    name = "commit-poet"
    internal = False
    commit_template = "{line}"

    def __init__(
        self,
        *,
        ollama_url: str | None = None,
        ollama_model: str | None = None,
        context_lines: int | None = None,
        timeout: float | None = None,
    ):
        super().__init__()
        self.ollama_url = (
            ollama_url or os.environ.get("OLLAMA_URL", "http://localhost:1601")
        ).rstrip("/")
        self.ollama_model = ollama_model or os.environ.get(
            "OLLAMA_MODEL", "qwen2.5:7b"
        )
        self.context_lines = int(
            context_lines if context_lines is not None else os.environ.get("CONTEXT_LINES", "10")
        )
        self.timeout = float(
            timeout if timeout is not None else os.environ.get("OLLAMA_TIMEOUT", str(_DEFAULT_TIMEOUT_SECONDS))
        )

    def _poem_path(self, plugin_dir: str) -> str:
        return os.path.join(plugin_dir, "poem.txt")

    def _poem_log_path(self, plugin_dir: str) -> str:
        return os.path.join(plugin_dir, "poem_log.jsonl")

    def _read_recent_lines(self, plugin_dir: str) -> list[str]:
        """Return the last ``context_lines`` non-blank lines from ``poem.txt``."""
        path = self._poem_path(plugin_dir)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
        return lines[-self.context_lines :] if self.context_lines > 0 else []

    @staticmethod
    def _build_prompt(recent_lines: list[str]) -> str:
        """Build a prompt that asks for exactly one new poem line."""
        if recent_lines:
            lines_block = "\n".join(recent_lines)
        else:
            lines_block = "(none yet — start the poem)"

        return (
            "Continue the following poem with exactly one new line.\n"
            "Rules:\n"
            "- Write only the next line, no numbering, no explanation.\n"
            "- The line must be under 72 characters.\n"
            "- Do not repeat any of the recent lines verbatim.\n\n"
            "Recent lines:\n"
            f"{lines_block}\n\n"
            "New line:"
        )

    @staticmethod
    def _sanitize_response(text: str) -> str:
        """Take the first non-empty line, clean markdown wrappers, and truncate."""
        for candidate in text.splitlines():
            candidate = candidate.strip()
            if candidate:
                candidate = _strip_markdown_wrappers(candidate)
                if candidate:
                    return candidate[:72]
        return ""

    def _parse_ollama_response(self, raw: bytes) -> tuple[str, int | None]:
        """Parse the JSON returned by Ollama's /api/generate endpoint."""
        data = json.loads(raw)
        text = data.get("response", "")
        token_count = data.get("eval_count")
        return text, token_count

    def _query_ollama(self, prompt: str) -> tuple[str, int | None, bool]:
        """Call Ollama and return ``(line, token_count, fallback_used)``.

        On any failure — network error, timeout, bad JSON, or empty output —
        the fallback line is returned with ``fallback_used=True``.
        """
        url = f"{self.ollama_url}/api/generate"
        body = json.dumps(
            {"model": self.ollama_model, "prompt": prompt, "stream": False}
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except Exception as exc:  # pragma: no cover - network paths exercised via mocks
            print(
                f"WARNING: Ollama request failed ({type(exc).__name__}: {exc}); "
                "using fallback line",
                file=sys.stderr,
            )
            return _FALLBACK_LINE, None, True

        try:
            text, token_count = self._parse_ollama_response(raw)
        except Exception as exc:  # pragma: no cover
            print(
                f"WARNING: could not parse Ollama response ({type(exc).__name__}: {exc}); "
                "using fallback line",
                file=sys.stderr,
            )
            return _FALLBACK_LINE, None, True

        line = self._sanitize_response(text)
        if not line:
            print(
                "WARNING: Ollama returned an empty line; using fallback line",
                file=sys.stderr,
            )
            return _FALLBACK_LINE, None, True

        return line, token_count, False

    def _generate_line(self, plugin_dir: str) -> tuple[str, int | None, bool]:
        """Ask Ollama for a new line, retry once on exact repeats."""
        recent = self._read_recent_lines(plugin_dir)
        prompt = self._build_prompt(recent)

        line, token_count, fallback_used = self._query_ollama(prompt)

        if not fallback_used and line in recent:
            # One retry.  If the model still repeats, we accept the honest
            # outcome rather than looping forever.
            line, token_count, fallback_used = self._query_ollama(prompt)

        return line, token_count, fallback_used

    def _append_poem_line(self, plugin_dir: str, line: str) -> None:
        path = self._poem_path(plugin_dir)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _append_poem_log(self, plugin_dir: str, entry: dict) -> None:
        path = self._poem_log_path(plugin_dir)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":"), sort_keys=True) + "\n")

    def produce(self) -> dict:
        """Generate the next poem line and update local poem files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        line, token_count, fallback_used = self._generate_line(plugin_dir)

        self._append_poem_line(plugin_dir, line)

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.ollama_model,
            "line": line,
            "token_count": token_count,
            "fallback_used": fallback_used,
        }
        self._append_poem_log(plugin_dir, log_entry)

        return {
            "line": line,
            "fallback_used": fallback_used,
            "model": self.ollama_model,
            "token_count": token_count,
        }
