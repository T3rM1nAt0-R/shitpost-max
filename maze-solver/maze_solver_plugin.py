import json
import os
import random
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from harness.shitpost_base import Shitpost


class MazeSolverPlugin(Shitpost):
    """Generate a random maze and solve it with BFS, DFS, A*."""

    name = "maze-solver"
    internal = False
    commit_template = "maze-solver: {size}x{size} — BFS {bfs_path_len} ({bfs_visited} visited), DFS {dfs_path_len} ({dfs_visited} visited), A* {astar_path_len} ({astar_visited} visited)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "maze_state.json"

    def _load_state(self, plugin_dir: str) -> Dict:
        """Load the running maze state, or initialise it at a random seed."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: maze state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"seed", "size", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: maze state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> Dict:
        return {
            "seed": random.randint(0, 1000000),
            "size": 21,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: Dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _generate_maze(self, size: int, seed: int) -> List[List[int]]:
        """Generate a solvable maze using the Aldous-Broder algorithm."""
        random.seed(seed)
        maze = [[0] * size for _ in range(size)]
        x, y = 1, 1
        while True:
            maze[x][y] = 1
            neighbors = []
            if x > 1 and maze[x-2][y] == 0: neighbors.append((x-2, y))
            if x < size-2 and maze[x+2][y] == 0: neighbors.append((x+2, y))
            if y > 1 and maze[x][y-2] == 0: neighbors.append((x, y-2))
            if y < size-2 and maze[x][y+2] == 0: neighbors.append((x, y+2))
            if not neighbors:
                break
            nx, ny = random.choice(neighbors)
            maze[(x + nx) // 2][(y + ny) // 2] = 1
            x, y = nx, ny
        return maze

    def _solve_maze(self, maze: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, int]:
        """Solve the maze using BFS, DFS, and A*."""
        from collections import deque
        import heapq

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        def bfs(start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, int]:
            queue = deque([(start, 0)])
            visited = set()
            while queue:
                (x, y), steps = queue.popleft()
                if (x, y) == goal:
                    return {"path_len": steps, "visited": len(visited)}
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < len(maze) and 0 <= ny < len(maze[0]) and maze[nx][ny] == 1 and (nx, ny) not in visited:
                        queue.append(((nx, ny), steps + 1))
                        visited.add((nx, ny))
            return {"path_len": -1, "visited": len(visited)}

        def dfs(start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, int]:
            stack = [(start, 0)]
            visited = set()
            while stack:
                (x, y), steps = stack.pop()
                if (x, y) == goal:
                    return {"path_len": steps, "visited": len(visited)}
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < len(maze) and 0 <= ny < len(maze[0]) and maze[nx][ny] == 1 and (nx, ny) not in visited:
                        stack.append(((nx, ny), steps + 1))
                        visited.add((nx, ny))
            return {"path_len": -1, "visited": len(visited)}

        def astar(start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, int]:
            open_list = []
            heapq.heappush(open_list, (0, start, 0))
            visited = set()
            while open_list:
                _, (x, y), steps = heapq.heappop(open_list)
                if (x, y) == goal:
                    return {"path_len": steps, "visited": len(visited)}
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < len(maze) and 0 <= ny < len(maze[0]) and maze[nx][ny] == 1 and (nx, ny) not in visited:
                        heapq.heappush(open_list, (steps + abs(nx - goal[0]) + abs(ny - goal[1]), (nx, ny), steps + 1))
                        visited.add((nx, ny))
            return {"path_len": -1, "visited": len(visited)}

        start = (1, 1)
        goal = (size-2, size-2)
        return {
            "bfs": bfs(start, goal),
            "dfs": dfs(start, goal),
            "astar": astar(start, goal),
        }

    def produce(self) -> Dict:
        """Return the maze and its solutions."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        size = state["size"]
        seed = state["seed"]

        maze = self._generate_maze(size, seed)
        solutions = self._solve_maze(maze, (1, 1), (size-2, size-2))

        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "seed": seed,
            "size": size,
            "maze": maze,
            "solutions": solutions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
