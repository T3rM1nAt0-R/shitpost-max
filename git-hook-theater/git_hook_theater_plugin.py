import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class GitHookTheaterPlugin(Shitpost):
    """Check the repo's own generated content for linting errors."""

    name = "git-hook-theater"
    internal = False
    commit_template = "hook: {status}, {n} files checked"

    def __init__(self):
        super().__init__()
        self._report_file_name = "hook_report.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._report_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    report = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: hook report file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
            return report

        return []

    def _save_state(self, plugin_dir: str, report: list) -> None:
        path = os.path.join(plugin_dir, self._report_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(report, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Run the pre-commit hook and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        report = self._load_state(plugin_dir)

        # Run the pre-commit hook
        passed = True
        errors = []
        bypassed = False

        if "GIT_COMMIT_NO_VERIFY" in os.environ:
            bypassed = True
        else:
            try:
                import subprocess
                result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
                files = result.stdout.splitlines()
                for file in files:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                        if content.endswith("\n"):
                            continue
                        errors.append(f"{file}: missing newline at EOF")
                        passed = False

                    if len(content) > 1024 * 1024:
                        errors.append(f"{file}: file size exceeds 1 MB")
                        passed = False

                    if any(line.endswith(" ") for line in content.splitlines()):
                        errors.append(f"{file}: trailing whitespace found")
                        passed = False
            except Exception as e:
                errors.append(str(e))
                passed = False

        # Append the result to the report
        commit_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        timestamp = datetime.now(timezone.utc).isoformat()
        report.append({
            "timestamp": timestamp,
            "commit_hash": commit_hash,
            "passed": passed,
            "errors": errors if not bypassed else None,
            "bypassed": bypassed
        })

        self._save_state(plugin_dir, report)

        return {
            "tick": len(report),
            "status": "passed" if passed else "failed",
            "n": len(files),
            "timestamp": timestamp,
        }
