#!/usr/bin/env python3
"""Regenerate dashboard/static/gitpostmax_catalog.json from live plugin
introspection, using the same docstrings and category grouping as the
README's plugin table (tools/generate_plugin_table.py / plugin_categories.json)
so the public repo and the shitpostmax.com dashboard never drift apart on
descriptions or which category a plugin lives in.

Found drifted 2026-07-16: gitpostmax_catalog.json was hand-maintained and
still referenced a "crash-service" plugin that had been renamed to
"selfhealing-demo" -- this script removes that failure mode by generating
the file instead of hand-editing it.

Usage: python3 tools/generate_gitpostmax_catalog.py [--out PATH]
"""

import argparse
import json
from pathlib import Path

from generate_plugin_table import (
    REPO_ROOT,
    CATEGORIES_PATH,
    collect_plugin_rows,
    load_categories,
)

DEFAULT_OUT = Path("/opt/data/tools/dashboard/static/gitpostmax_catalog.json")


def build_catalog(repo_root: Path = REPO_ROOT, categories_path: Path = CATEGORIES_PATH) -> dict:
    row_map = dict(collect_plugin_rows(repo_root))
    categories = load_categories(categories_path)

    categorized = {name for cat in categories for name in cat["plugins"]}
    uncategorized = set(row_map) - categorized
    if uncategorized:
        raise ValueError(f"plugins missing from plugin_categories.json: {sorted(uncategorized)}")
    unknown = categorized - set(row_map)
    if unknown:
        raise ValueError(f"plugin_categories.json references unknown/internal plugins: {sorted(unknown)}")

    return {
        "categories": [
            {
                "name": cat["name"],
                "plugins": [
                    {"name": name, "description": row_map[name]}
                    for name in cat["plugins"]
                ],
            }
            for cat in categories
        ]
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    catalog = build_catalog()
    args.out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(len(c["plugins"]) for c in catalog["categories"])
    print(f"wrote {args.out} ({len(catalog['categories'])} categories, {total} plugins)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
