"""Builds ``live/live.json``: each plugin's most recent commit message and time.

The public site fetches this one small file (via raw.githubusercontent.com) to
show what the fleet is doing right now, instead of 180 separate requests.
A scheduler job (see ``harness/scheduler.py``) refreshes and commits it every
few minutes; the normal push job publishes it.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness.shitpost_base import _repo_git_lock

LIVE_FILE = "live/live.json"
# Newest commits to scan per refresh. Plugins that tick less often than the
# window covers keep the entry from an earlier refresh.
SCAN_COMMITS = 3000
MAX_MESSAGE_CHARS = 120

_SEP = "\x01"


def _plugin_dirs(repo_root: Path) -> set[str]:
    return {p.parent.name for p in repo_root.glob("*/tick.py")}


def collect(repo_root: Path, existing: dict | None = None) -> dict:
    """Return ``{slug: {"m": message, "t": iso time}}``, newest commit per plugin."""
    result = subprocess.run(
        [
            "git", "log", f"-n{SCAN_COMMITS}", "--no-merges",
            f"--format={_SEP}%cI{_SEP}%s", "--name-only",
        ],
        cwd=repo_root, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    plugins = _plugin_dirs(repo_root)
    services = dict(existing or {})
    seen: set[str] = set()
    when = message = None
    for line in result.stdout.splitlines():
        if line.startswith(_SEP):
            _, when, message = line.split(_SEP, 2)
        elif "/" in line and when is not None:
            slug = line.split("/", 1)[0]
            if slug in plugins and slug not in seen:
                seen.add(slug)
                services[slug] = {"m": message[:MAX_MESSAGE_CHARS], "t": when}
    return {slug: services[slug] for slug in sorted(services) if slug in plugins}


def refresh(repo_root: Path) -> bool:
    """Rewrite live/live.json and commit it if anything changed. Returns True if committed."""
    path = repo_root / LIVE_FILE
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8")).get("services", {})
        except (ValueError, OSError):
            existing = {}
    services = collect(repo_root, existing)
    if not services:
        return False
    if services == existing:
        return False

    payload = {"updated": datetime.now(timezone.utc).isoformat(), "services": services}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)

    with _repo_git_lock(str(repo_root / ".git-push.lock")):
        subprocess.run(["git", "add", "-f", LIVE_FILE], cwd=repo_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"live: {len(services)} services", "--", LIVE_FILE],
            cwd=repo_root, check=True,
        )
    return True


def live_job(repo_root: Path) -> None:
    """Scheduler job wrapper: logs instead of crashing the scheduler."""
    try:
        refresh(repo_root)
    except Exception as exc:
        print(f"[live] refresh failed: {exc}", file=sys.stderr)
