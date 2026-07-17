#!/usr/bin/env python3
"""Regenerate the plugin table in README.md from live plugin introspection.

Each plugin is inspected in a short-lived subprocess so its module is never
imported into this script's own process (avoiding module-name collisions and
import-time side effects). The table is written between marker comments in
README.md so there is a single source of truth.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
CATEGORIES_PATH = REPO_ROOT / "tools" / "plugin_categories.json"

# Directories that are never plugin directories.
SKIP_DIRS = {
    "harness",
    "tests",
    "tools",
    "scripts",
    ".venv",
    ".git",
    ".github",
    ".githooks",
    ".pytest_cache",
}

MARKER_START = "<!-- PLUGIN_TABLE_START -->"
MARKER_END = "<!-- PLUGIN_TABLE_END -->"


class PluginTableError(RuntimeError):
    """Raised when the plugin table cannot be generated."""


_INTROSPECT_SCRIPT = r"""
import importlib.util
import json
import os
import sys

repo_root = sys.argv[1]
plugin_dir = sys.argv[2]
plugin_name = os.path.basename(plugin_dir)
sys.path.insert(0, repo_root)

plugin_files = sorted(
    f for f in os.listdir(plugin_dir)
    if f.endswith(".py")
    and f != "tick.py"
    and f != "__init__.py"
)

if not plugin_files:
    print("expected at least 1 plugin module in %s, found 0" % plugin_name, file=sys.stderr)
    sys.exit(1)

from harness.shitpost_base import Shitpost  # noqa: E402

# Relaxed 2026-07-13: a plugin's logic may reasonably span more than one file
# (e.g. a separate cache class or workload generator alongside the Shitpost
# subclass itself) -- import every non-tick/test module in the directory and
# look for the Shitpost subclass across all of them, rather than requiring
# exactly one file. Still require exactly one Shitpost subclass total, so a
# plugin can't accidentally define (or fail to define) its entrypoint class.
all_candidates = []  # list of (class, owning_module) pairs
for fname in plugin_files:
    module_path = os.path.join(plugin_dir, fname)
    module_name = fname.replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    candidates = [
        obj for name in dir(mod)
        if isinstance((obj := getattr(mod, name)), type)
        and issubclass(obj, Shitpost)
        and obj is not Shitpost
    ]
    for c in candidates:
        all_candidates.append((c, mod))

# Dedup by the class's own declared `name` attribute (its real plugin
# identity), not Python object identity -- a second entrypoint file that
# isn't literally called tick.py but imports the real plugin class to call
# run_tick() re-imports it as a genuinely separate object (Python doesn't
# cache across two independent spec_from_file_location loads under different
# module names), so id()-based dedup does NOT catch this in practice
# (verified directly against crypto-tick's real run.py, 2026-07-13).
#
# Prefer whichever module actually *defines* the class (c.__module__ ==
# mod.__name__) over one that merely imports/re-exports it -- otherwise
# which module's docstring ends up in the table depends on directory listing
# order, which os.listdir() does not guarantee is stable across filesystems,
# making the generated README non-deterministic between environments
# (caught 2026-07-14: crypto-tick's table entry differed between a local run
# and CI purely from listdir ordering, failing the --check step every time).
by_name = {}
for c, mod in all_candidates:
    name = getattr(c, "name", None)
    defines_it = getattr(c, "__module__", None) == mod.__name__
    if name not in by_name or (defines_it and not by_name[name][2]):
        by_name[name] = (c, mod, defines_it)
all_candidates = [(c, mod) for c, mod, _ in by_name.values()]

if len(all_candidates) != 1:
    print(
        "expected 1 Shitpost subclass across %s (%s), found %d"
        % (plugin_name, plugin_files, len(all_candidates)),
        file=sys.stderr,
    )
    sys.exit(1)

cls, owning_module = all_candidates[0]
doc = owning_module.__doc__ or ""
first_line = doc.strip().splitlines()[0].strip() if doc.strip() else ""
print(json.dumps({"name": cls.name, "internal": cls.internal, "description": first_line}))
"""


def discover_plugin_dirs(repo_root: Path) -> list[str]:
    """Return sorted plugin directory names, excluding special directories."""
    return sorted(
        entry.name
        for entry in repo_root.iterdir()
        if entry.is_dir()
        and not entry.name.startswith(".")
        and entry.name not in SKIP_DIRS
    )


def introspect_plugin(repo_root: Path, plugin_dir_name: str) -> dict:
    """Run a subprocess to read a plugin's name, internal flag, and docstring.

    Returns ``{"name": str, "internal": bool, "description": str}`` on
    success. Raises :class:`PluginTableError` if introspection fails.
    """
    plugin_dir = repo_root / plugin_dir_name
    try:
        result = subprocess.run(
            [sys.executable, "-c", _INTROSPECT_SCRIPT, str(repo_root), str(plugin_dir)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(plugin_dir),
        )
    except subprocess.TimeoutExpired as exc:
        raise PluginTableError(f"introspection timed out for {plugin_dir_name}") from exc
    except OSError as exc:
        raise PluginTableError(f"could not introspect {plugin_dir_name}: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise PluginTableError(
            f"introspection failed for {plugin_dir_name}: "
            f"{stderr or result.stdout.strip()}"
        )

    try:
        data = json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise PluginTableError(
            f"introspection output for {plugin_dir_name} is not valid JSON: {exc}"
        ) from exc

    return data


def collect_plugin_rows(repo_root: Path) -> list[tuple[str, str]]:
    """Return (plugin_name, description) rows for all public plugins."""
    rows: list[tuple[str, str]] = []
    for plugin_dir_name in discover_plugin_dirs(repo_root):
        meta = introspect_plugin(repo_root, plugin_dir_name)
        if meta is None:
            continue
        if meta.get("internal"):
            continue
        rows.append((meta["name"], meta.get("description", "")))
    return rows


def load_categories(categories_path: Path) -> list[dict]:
    """Load the category -> ordered plugin-name-list mapping.

    This is the single source of truth for grouping shared with
    tools/generate_gitpostmax_catalog.py -- keep both generators reading
    the same file so the README and the /gitpostmax dashboard never drift
    out of sync on which category a plugin lives in (a real mismatch, not
    hypothetical: gitpostmax_catalog.json referenced a "crash-service"
    plugin that had been renamed to "selfhealing-demo", caught 2026-07-16).
    """
    return json.loads(categories_path.read_text(encoding="utf-8"))["categories"]


def format_table(rows: list[tuple[str, str]], categories_path: Path = CATEGORIES_PATH) -> str:
    """Format rows as collapsible per-category markdown tables.

    Raises ValueError if a public plugin isn't assigned to exactly one
    category, or a category lists a plugin that isn't a real public row --
    both indicate plugin_categories.json has drifted from the live plugin
    set and needs a human to reconcile it, not a silent skip.

    Falls back to a single flat table (the pre-categorization behavior) if
    categories_path doesn't exist at all -- keeps this usable against an
    isolated/synthetic repo root (as several tests construct) that has no
    reason to carry its own plugin_categories.json.
    """
    row_map = dict(rows)
    if not categories_path.exists():
        lines = ["Plugin | Description", "--- | ---"]
        for name, description in rows:
            lines.append(f"{name} | {description.replace('|', '\\|')}")
        return "\n".join(lines) + "\n"

    categories = load_categories(categories_path)

    categorized = {name for cat in categories for name in cat["plugins"]}
    uncategorized = set(row_map) - categorized
    if uncategorized:
        raise ValueError(f"plugins missing from plugin_categories.json: {sorted(uncategorized)}")
    unknown = categorized - set(row_map)
    if unknown:
        raise ValueError(f"plugin_categories.json references unknown/internal plugins: {sorted(unknown)}")

    blocks = []
    for cat in categories:
        lines = ["Plugin | Description", "--- | ---"]
        for name in cat["plugins"]:
            safe_description = row_map[name].replace("|", "\\|")
            lines.append(f"{name} | {safe_description}")
        table = "\n".join(lines)
        blocks.append(
            f"<details>\n<summary><strong>{cat['name']}</strong> "
            f"<sub>({len(cat['plugins'])})</sub></summary>\n\n{table}\n\n</details>"
        )
    return "\n\n".join(blocks) + "\n"


def regenerate_readme(readme_path: Path, table: str) -> str:
    """Return README content with the table section replaced."""
    content = readme_path.read_text(encoding="utf-8")
    start_count = content.count(MARKER_START)
    end_count = content.count(MARKER_END)
    if start_count != 1 or end_count != 1:
        raise ValueError(
            f"{readme_path} must contain exactly one {MARKER_START} marker "
            f"(found {start_count}) and exactly one {MARKER_END} marker "
            f"(found {end_count})"
        )

    start_idx = content.find(MARKER_START)
    end_idx = content.find(MARKER_END)
    if end_idx < start_idx:
        raise ValueError("End marker appears before start marker")

    before = content[: start_idx + len(MARKER_START)]
    after = content[end_idx:]
    return f"{before}\n\n{table}\n{after}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate the public plugin table in README.md."
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=README_PATH,
        help="Path to README.md (default: %(default)s)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed table is stale instead of writing.",
    )
    args = parser.parse_args(argv)

    try:
        rows = collect_plugin_rows(REPO_ROOT)
        table = format_table(rows, categories_path=REPO_ROOT / "tools" / "plugin_categories.json")

        if args.check:
            current = args.readme.read_text(encoding="utf-8")
            expected = regenerate_readme(args.readme, table)
            if current != expected:
                print(
                    f"ERROR: {args.readme} plugin table is stale. "
                    "Run 'python3 tools/generate_plugin_table.py' to regenerate it.",
                    file=sys.stderr,
                )
                return 1
            return 0

        expected = regenerate_readme(args.readme, table)
        args.readme.write_text(expected, encoding="utf-8")
        return 0
    except (PluginTableError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
