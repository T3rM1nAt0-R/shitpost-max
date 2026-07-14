import ast
import shutil
import tempfile
from pathlib import Path

from tools.generate_plugin_table import (
    MARKER_END,
    MARKER_START,
    README_PATH,
    REPO_ROOT,
    collect_plugin_rows,
    discover_plugin_dirs,
    introspect_plugin,
    main,
)

KNOWN_PUBLIC_PLUGINS = {
    "base-converter",
    "commit-poet",
    "fibonacci-full",
    "golden-ratio",
    "pi-spigot",
}


def _first_docstring_line(plugin_dir_name: str) -> str:
    """Read the first line of the module docstring from the plugin's main file."""
    plugin_path = REPO_ROOT / plugin_dir_name
    candidates = [
        f
        for f in plugin_path.iterdir()
        if f.suffix == ".py"
        and f.name != "tick.py"
        and not f.name.startswith("test")
        and f.name != "__init__.py"
    ]
    assert len(candidates) == 1, f"expected 1 plugin module in {plugin_dir_name}"
    module_path = candidates[0]
    source = module_path.read_text(encoding="utf-8")
    doc = ast.get_docstring(ast.parse(source))
    assert doc, f"{module_path} is missing a module docstring"
    return doc.strip().splitlines()[0].strip()


def test_discover_plugin_dirs_includes_known_public_plugins():
    dirs = set(discover_plugin_dirs(REPO_ROOT))
    assert KNOWN_PUBLIC_PLUGINS <= dirs
    # tunnel-health is an arbitrary still-existing internal plugin, just
    # confirming discovery finds internal dirs too, not only public ones
    # (uptime-witness used to be the example here, retired 2026-07-14
    # in favor of the already-live Uptime Kuma instance).
    assert "tunnel-health" in dirs
    assert "harness" not in dirs
    assert "tests" not in dirs
    assert "tools" not in dirs


def test_public_plugins_appear_with_real_docstring_descriptions():
    rows = dict(collect_plugin_rows(REPO_ROOT))
    assert set(rows) == KNOWN_PUBLIC_PLUGINS

    for plugin_dir_name in KNOWN_PUBLIC_PLUGINS:
        meta = introspect_plugin(REPO_ROOT, plugin_dir_name)
        assert meta is not None
        assert meta["internal"] is False
        expected_description = _first_docstring_line(plugin_dir_name)
        assert meta["name"] in rows
        assert rows[meta["name"]] == expected_description
        assert rows[meta["name"]] != ""


def test_internal_plugin_is_skipped():
    rows = dict(collect_plugin_rows(REPO_ROOT))
    assert "tunnel-health" not in rows


def test_check_passes_when_readme_is_fresh():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        readme = Path(f.name)
    try:
        shutil.copy(README_PATH, readme)
        assert main(["--readme", str(readme)]) == 0
        assert main(["--readme", str(readme), "--check"]) == 0
    finally:
        readme.unlink(missing_ok=True)


def test_check_fails_when_table_is_stale():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        readme = Path(f.name)
    try:
        shutil.copy(README_PATH, readme)
        assert main(["--readme", str(readme)]) == 0
        stale_content = readme.read_text(encoding="utf-8").replace(
            "Pi spigot plugin", "Pee spigot plugin"
        )
        readme.write_text(stale_content, encoding="utf-8")
        assert main(["--readme", str(readme), "--check"]) == 1
    finally:
        readme.unlink(missing_ok=True)


def test_two_plugin_modules_causes_hard_failure(tmp_path, monkeypatch, capsys):
    import tools.generate_plugin_table as gpt

    plugin_dir = tmp_path / "bad-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "one.py").write_text("# one\n", encoding="utf-8")
    (plugin_dir / "two.py").write_text("# two\n", encoding="utf-8")

    monkeypatch.setattr(gpt, "REPO_ROOT", tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text(f"{MARKER_START}\n\n{MARKER_END}\n", encoding="utf-8")

    assert main(["--readme", str(readme)]) == 1
    err = capsys.readouterr().err
    assert "bad-plugin" in err
    assert "found 2" in err


def test_duplicate_marker_causes_hard_failure(tmp_path, monkeypatch, capsys):
    import tools.generate_plugin_table as gpt

    monkeypatch.setattr(gpt, "REPO_ROOT", tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text(
        f"intro\n{MARKER_START}\n\n{MARKER_END}\n"
        f"example:\n{MARKER_START}\n\n{MARKER_END}\n",
        encoding="utf-8",
    )

    assert main(["--readme", str(readme)]) == 1
    err = capsys.readouterr().err
    assert "must contain exactly one" in err
    assert MARKER_START in err
