"""Revolutionizing spatial data indexing with an AI-optimized k-dimensional tree architecture. Every split divides the space more efficiently."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class KdtreeBuilderPlugin(Shitpost):
    """Insert 2D points incrementally into a k-d tree, one point per tick."""

    name = "kdtree-builder"
    internal = False
    commit_template = "kdtree +{point}: {node_count} nodes, depth {depth}"

    _POINTS = [(3, 6), (17, 15), (13, 15), (6, 12), (9, 1), (2, 7), (10, 19)]

    @staticmethod
    def _insert(root, point, depth=0):
        if root is None:
            return {"point": list(point), "left": None, "right": None}
        axis = depth % 2
        if point[axis] < root["point"][axis]:
            root["left"] = KdtreeBuilderPlugin._insert(root["left"], point, depth + 1)
        else:
            root["right"] = KdtreeBuilderPlugin._insert(root["right"], point, depth + 1)
        return root

    @staticmethod
    def _count_nodes(node) -> int:
        if node is None:
            return 0
        return 1 + KdtreeBuilderPlugin._count_nodes(node["left"]) + KdtreeBuilderPlugin._count_nodes(node["right"])

    @staticmethod
    def _tree_depth(node) -> int:
        if node is None:
            return 0
        return 1 + max(KdtreeBuilderPlugin._tree_depth(node["left"]), KdtreeBuilderPlugin._tree_depth(node["right"]))

    def produce(self) -> dict:
        """Insert the next point into the k-d tree and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "root": None,
            "point_index": 0,
            "tick": 0,
        })

        point = self._POINTS[state["point_index"] % len(self._POINTS)]
        state["root"] = self._insert(state["root"], point)
        node_count = self._count_nodes(state["root"])
        depth = self._tree_depth(state["root"])

        state["point_index"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "point": list(point),
            "node_count": node_count,
            "depth": depth,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
