import json
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from harness.shitpost_base import Shitpost


class MazeSolverPlugin(Shitpost):
    """Generate a random maze and solve it with BFS, DFS, A*."""

    name = "maze-solver"
    internal = False
    commit_template = "maze-solver: {size}x{size} — BFS {solutions[bfs][path_len]} ({solutions[bfs][visited]} visited), DFS {solutions[dfs][path_len]} ({solutions[dfs][visited]} visited), A* {solutions[astar][path_len]} ({solutions[astar][visited]} visited)"

    def __init__(self):
        super().__init__()

    def _load_persisted_state(self, default: Dict) -> Dict:
        """Load the running maze state, or initialise it at a random seed."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)
        state_path = os.path.join(plugin_dir, "state.json")
        if not os.path.exists(state_path):
            with open(state_path, "w") as f:
                json.dump(default, f)
        with open(state_path, "r") as f:
            return json.load(f)

    def _save_persisted_state(self, state: Dict) -> None:
        """Atomically persists the state dict."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)
        state_path = os.path.join(plugin_dir, "state.json")
        with open(state_path, "w") as f:
            json.dump(state, f)

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
        goal = (len(maze)-2, len(maze[0])-2)
        return {
            "bfs": bfs(start, goal),
            "dfs": dfs(start, goal),
            "astar": astar(start, goal),
        }

    def produce(self) -> Dict:
        """Return the maze and its solutions."""
        state = self._load_persisted_state({
            "seed": random.randint(0, 1000000),
            "size": 21,
            "tick": 0,
        })

        size = state["size"]
        seed = state["seed"]

        maze = self._generate_maze(size, seed)
        solutions = self._solve_maze(maze, (1, 1), (size-2, size-2))

        state["tick"] += 1

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "seed": seed,
            "size": size,
            "maze": maze,
            "solutions": solutions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
