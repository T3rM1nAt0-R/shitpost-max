"""Checks a fixed embedded pair of Dockerfiles for common anti-patterns, cycling through them."""

import re

from harness.shitpost_base import Shitpost

DOCKERFILES = [
    ("good.Dockerfile", "FROM python:3.11-slim\nCOPY . /app\nWORKDIR /app\nRUN pip install --no-cache-dir -r requirements.txt\nUSER appuser\nCMD [\"python\", \"main.py\"]\n"),
    ("bad.Dockerfile", "FROM ubuntu:latest\nADD . /app\nRUN apt-get install curl\nCMD python main.py\n"),
]


def _lint(content):
    issues = []
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r"^FROM\s+\S+:latest\b", stripped):
            issues.append((i, "uses ':latest' tag instead of a pinned version"))
        if re.match(r"^ADD\s+", stripped) and not re.search(r"https?://|\.tar", stripped):
            issues.append((i, "uses ADD for local files instead of COPY"))
        if re.match(r"^RUN\s+apt-get install", stripped) and "--no-install-recommends" not in stripped:
            issues.append((i, "apt-get install without --no-install-recommends"))
    if not any(re.match(r"^USER\s+", line.strip()) for line in lines):
        issues.append((0, "no USER instruction; container runs as root"))
    return issues


class DockerfileLinterPlugin(Shitpost):
    """Emit lint issues for one DOCKERFILES entry per tick, cycling through the list."""

    name = "dockerfile-linter"
    internal = False
    commit_template = "dockerfile-lint {filename}: {issue_count} issues"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        filename, content = DOCKERFILES[index]
        issues = _lint(content)

        result = {
            "filename": filename,
            "issue_count": len(issues),
            "issues": issues,
        }

        self._save_persisted_state({"index": (index + 1) % len(DOCKERFILES)})

        return result
