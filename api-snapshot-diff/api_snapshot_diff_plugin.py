"""Simulates an API snapshot diff between two fixed embedded JSON snapshots. No live network call."""

from harness.shitpost_base import Shitpost

BEFORE = {"status": "ok", "version": "1.0", "users": 100, "region": "us-east"}
AFTER = {"status": "ok", "version": "1.1", "users": 142}


def _diff(before, after):
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in before if k in after and before[k] != after[k])
    return added, removed, changed


class ApiSnapshotDiffPlugin(Shitpost):
    """Emit the added/removed/changed key diff every tick (stateless, constant result)."""

    name = "api-snapshot-diff"
    internal = False
    commit_template = "api-diff: +{added} -{removed} ~{changed}"

    def produce(self) -> dict:
        added, removed, changed = _diff(BEFORE, AFTER)
        return {"added": added, "removed": removed, "changed": changed}
