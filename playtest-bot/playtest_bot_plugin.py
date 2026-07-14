import itertools
import json
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from harness.shitpost_base import Shitpost

# --- 2048 game constants ---
_SIZE = 4
_NEW_TILE_VALUES = [2, 2, 2, 2, 4]  # 80 % chance of 2, 20 % chance of 4
_MOVE_DIRS = ["left", "right", "up", "down"]


def _empty_board() -> List[List[int]]:
    """Return a 4x4 grid of zeros."""
    return [[0] * _SIZE for _ in range(_SIZE)]


def _clone_board(board: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in board]


def _vacant_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    return [
        (r, c) for r in range(_SIZE) for c in range(_SIZE) if board[r][c] == 0
    ]


def _spawn_tile(board: List[List[int]]) -> bool:
    """Place a 2 or 4 in a random vacant cell.  Returns False if board is full."""
    cells = _vacant_cells(board)
    if not cells:
        return False
    r, c = random.choice(cells)
    board[r][c] = random.choice(_NEW_TILE_VALUES)
    return True


def _slide_row(row: List[int]) -> Tuple[List[int], int]:
    """Slide and merge one row leftwards.  Returns (new_row, points_earned)."""
    # Remove zeros, keeping order.
    tiles = [v for v in row if v != 0]
    merged = []
    points = 0
    skip = False
    for i in range(len(tiles)):
        if skip:
            skip = False
            continue
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            merged.append(tiles[i] * 2)
            points += tiles[i] * 2
            skip = True
        else:
            merged.append(tiles[i])
    merged += [0] * (_SIZE - len(merged))
    return merged, points


def _apply_move(board: List[List[int]], direction: str) -> Tuple[List[List[int]], int]:
    """Return (new_board, points_earned) for the given move."""
    b = _clone_board(board)
    points = 0

    if direction == "left":
        for r in range(_SIZE):
            b[r], p = _slide_row(b[r])
            points += p
    elif direction == "right":
        for r in range(_SIZE):
            rev = list(reversed(b[r]))
            slid, p = _slide_row(rev)
            b[r] = list(reversed(slid))
            points += p
    elif direction == "up":
        for c in range(_SIZE):
            col = [b[r][c] for r in range(_SIZE)]
            slid, p = _slide_row(col)
            for r in range(_SIZE):
                b[r][c] = slid[r]
            points += p
    elif direction == "down":
        for c in range(_SIZE):
            col = [b[r][c] for r in range(_SIZE)]
            rev = list(reversed(col))
            slid, p = _slide_row(rev)
            slid_rev = list(reversed(slid))
            for r in range(_SIZE):
                b[r][c] = slid_rev[r]
            points += p
    return b, points


def _valid_moves(board: List[List[int]]) -> List[str]:
    """Return the list of directions that change the board."""
    valid = []
    for d in _MOVE_DIRS:
        new_b, _ = _apply_move(board, d)
        if new_b != board:
            valid.append(d)
    return valid


def _max_tile(board: List[List[int]]) -> int:
    return max(itertools.chain.from_iterable(board))


# ---- heuristic scoring for a board (used by the heuristic agent) ----

_SNAKE_WEIGHTS = [
    [256, 128, 64, 32],
    [16, 8, 4, 2],
    [1, 0.5, 0.25, 0.125],
    [0.0625, 0.03125, 0.015625, 0.0078125],
]


def _score_board(board: List[List[int]]) -> float:
    """Weighted sum preferring big tiles in the top-left snake corner."""
    return sum(
        board[r][c] * _SNAKE_WEIGHTS[r][c]
        for r in range(_SIZE)
        for c in range(_SIZE)
    )


# ---- public helpers (exported for testing) ----


def _max_tile_board(board: List[List[int]]) -> int:
    return _max_tile(board)


# ---- 2048 game driver ----

_MAX_MOVES = 20_000


def _play_2048(move_selector) -> Dict[str, int]:
    """Play one full 2048 game using *move_selector* to pick each move.

    *move_selector* receives the current board and the list of valid move
    directions (guaranteed non-empty) and returns one of those directions.

    Returns ``{"final_score": ..., "max_tile": ..., "game_length": ...}``.
    """
    board = _empty_board()
    _spawn_tile(board)
    _spawn_tile(board)
    score = 0
    moves = 0

    for _ in range(_MAX_MOVES):
        valid = _valid_moves(board)
        if not valid:
            break  # Game over
        direction = move_selector(board, valid)
        board, pts = _apply_move(board, direction)
        score += pts
        moves += 1
        _spawn_tile(board)

    return {
        "final_score": score,
        "max_tile": _max_tile(board),
        "game_length": moves,
    }


def _random_move(board, valid: List[str]) -> str:
    """Pick a random valid move."""
    return random.choice(valid)


def _heuristic_move(board, valid: List[str]) -> str:
    """Pick the valid move that gives the best weighted board score."""
    best_d = valid[0]
    best_s = -1.0
    for d in valid:
        new_b, _ = _apply_move(board, d)
        s = _score_board(new_b)
        if s > best_s:
            best_s = s
            best_d = d
    return best_d


# ---- Plugin class ----


class PlaytestBotPlugin(Shitpost):
    """Play one game of 2048 per tick and log the final score."""

    name = "playtest-bot"
    internal = False
    commit_template = "playtest [{agent}]: score {final_score} max {max_tile} in {game_length} moves"

    def __init__(self):
        super().__init__()
        self._log_file_name = "playtest_log.jsonl"
        self._stats_file_name = "playtest_stats.json"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "playtest_state.json")

    def _append_log(self, plugin_dir: str, log_entry: Dict[str, int]) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def _update_stats(self, plugin_dir: str, stats: Dict[str, int]) -> None:
        path = os.path.join(plugin_dir, self._stats_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> Optional[Dict[str, int]]:
        """Return the result of playing one game and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"tick": 0, "agent": 0})
        tick = state["tick"]
        agent = state["agent"]

        # Alternate between heuristic and random agents
        if agent == 0:
            result = self._play_game_heuristic()
        else:
            result = self._play_game_random()

        log_entry = {
            "tick": tick,
            "agent": "heuristic" if agent == 0 else "random",
            **result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._append_log(plugin_dir, log_entry)

        # Update state
        state["tick"] += 1
        state["agent"] = 1 - agent  # Switch agent for next tick
        self._save_persisted_state(state)

        return {
            "tick": tick,
            "agent": "heuristic" if agent == 0 else "random",
            **result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _play_game_heuristic(self) -> Dict[str, int]:
        """Play one game using a heuristic agent."""
        return _play_2048(_heuristic_move)

    def _play_game_random(self) -> Dict[str, int]:
        """Play one game using a random agent."""
        return _play_2048(_random_move)
