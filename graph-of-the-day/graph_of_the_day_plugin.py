import json
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Set

from harness.shitpost_base import Shitpost


class GraphOfTheDayPlugin(Shitpost):
    """Generate a random graph and compute one graph-theoretic property per tick."""

    name = "graph-of-the-day"
    internal = False
    commit_template = "graph-of-the-day: {vertices}v/{edges}e — {property_name} = {property_value}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "graph_of_the_day_state.json"

    def _load_state(self, plugin_dir: str) -> Dict[str, int]:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: graph-of-the-day state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"vertices", "edges", "property_index"}
            if not required.issubset(state.keys()):
                print(
                    "warning: graph-of-the-day state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> Dict[str, int]:
        return {
            "vertices": 100,
            "edges": 30,
            "property_index": 0,
        }

    def _save_state(self, plugin_dir: str, state: Dict[str, int]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _generate_graph(self, vertices: int, edges: int) -> List[Set[int]]:
        """Generate a random undirected graph with the given number of vertices and edges."""
        if edges > (vertices * (vertices - 1)) // 2:
            raise ValueError("Too many edges for the given number of vertices")

        graph = [set() for _ in range(vertices)]
        added_edges = set()

        while len(added_edges) < edges:
            u, v = random.sample(range(vertices), 2)
            if u != v and (u, v) not in added_edges and (v, u) not in added_edges:
                graph[u].add(v)
                graph[v].add(u)
                added_edges.add((u, v))
                added_edges.add((v, u))

        return graph

    def _connected_components(self, graph: List[Set[int]]) -> int:
        """Compute the number of connected components in the graph."""
        visited = set()
        components = 0

        for vertex in range(len(graph)):
            if vertex not in visited:
                stack = [vertex]
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        stack.extend(neighbor for neighbor in graph[current] if neighbor not in visited)
                components += 1

        return components

    def _diameter(self, graph: List[Set[int]]) -> int:
        """Compute the diameter of the graph."""
        max_distance = 0

        for vertex in range(len(graph)):
            distances = [float('inf')] * len(graph)
            distances[vertex] = 0
            queue = [vertex]

            while queue:
                current = queue.pop(0)
                for neighbor in graph[current]:
                    if distances[neighbor] == float('inf'):
                        distances[neighbor] = distances[current] + 1
                        max_distance = max(max_distance, distances[neighbor])
                        queue.append(neighbor)

        return max_distance

    def _minimum_spanning_tree_weight(self, graph: List[Set[int]]) -> int:
        """Compute the weight of the minimum spanning tree using Kruskal's algorithm."""
        edges = []
        for u in range(len(graph)):
            for v in graph[u]:
                if (u, v) not in edges and (v, u) not in edges:
                    edges.append((u, v))

        edges.sort(key=lambda x: len(x[0]) + len(x[1]))

        parent = list(range(len(graph)))
        rank = [0] * len(graph)

        def find(vertex: int) -> int:
            if parent[vertex] != vertex:
                parent[vertex] = find(parent[vertex])
            return parent[vertex]

        def union(u: int, v: int) -> None:
            root_u = find(u)
            root_v = find(v)

            if rank[root_u] < rank[root_v]:
                parent[root_u] = root_v
            elif rank[root_u] > rank[root_v]:
                parent[root_v] = root_u
            else:
                parent[root_v] = root_u
                rank[root_u] += 1

        mst_weight = 0
        for u, v in edges:
            if find(u) != find(v):
                union(u, v)
                mst_weight += len(u) + len(v)

        return mst_weight

    def _degree_stats(self, graph: List[Set[int]]) -> Dict[str, float]:
        """Compute the minimum, maximum, and mean degree of the graph."""
        degrees = [len(neighborhood) for neighborhood in graph]
        min_degree = min(degrees)
        max_degree = max(degrees)
        mean_degree = sum(degrees) / len(degrees)

        return {
            "min": min_degree,
            "max": max_degree,
            "mean": mean_degree,
        }

    def _triangle_count(self, graph: List[Set[int]]) -> int:
        """Compute the number of triangles in the graph."""
        triangle_count = 0

        for u in range(len(graph)):
            for v in graph[u]:
                for w in graph[v]:
                    if w in graph[u]:
                        triangle_count += 1

        return triangle_count // 6

    def _maximum_clique_lower_bound(self, graph: List[Set[int]]) -> int:
        """Compute a lower bound on the size of the maximum clique using a greedy heuristic."""
        max_clique_size = 0
        vertices = list(range(len(graph)))

        while vertices:
            vertex = vertices.pop()
            neighborhood = set(vertices) & graph[vertex]
            if len(neighborhood) > max_clique_size:
                max_clique_size += 1
                vertices = [v for v in vertices if v not in neighborhood]

        return max_clique_size

    def produce(self) -> Dict[str, int]:
        """Generate a random graph and compute one property per tick."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        vertices = state["vertices"]
        edges = state["edges"]

        graph = self._generate_graph(vertices, edges)
        properties = [
            (self._connected_components, "Connected Components"),
            (self._diameter, "Diameter"),
            (self._minimum_spanning_tree_weight, "MST Weight"),
            (self._degree_stats, "Degree Stats"),
            (self._triangle_count, "Triangle Count"),
            (self._maximum_clique_lower_bound, "Max Clique Lower Bound"),
        ]

        property_index = state["property_index"]
        property_function, property_name = properties[property_index]

        if callable(property_function):
            result = property_function(graph)
            if isinstance(result, dict):
                property_value = f"{result['min']}-{result['max']}-{result['mean']}"
            else:
                property_value = str(result)

            state["property_index"] = (state["property_index"] + 1) % len(properties)
        else:
            property_value = "N/A"
            state["property_index"] = (state["property_index"] + 1) % len(properties)

        self._save_state(plugin_dir, state)

        return {
            "vertices": vertices,
            "edges": edges,
            "property_name": property_name,
            "property_value": property_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
