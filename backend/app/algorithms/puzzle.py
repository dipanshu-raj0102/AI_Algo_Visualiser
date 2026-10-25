from __future__ import annotations

import heapq
from itertools import count

from pydantic import BaseModel, Field, field_validator

from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


class PuzzleConfig(BaseModel):
    board: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 0, 15])
    max_expansions: int = Field(default=20_000, ge=1, le=100_000)

    @field_validator("board")
    @classmethod
    def validate_board(cls, value: list[int]) -> list[int]:
        if len(value) != 16 or set(value) != set(range(16)): raise ValueError("board must be a permutation of 0..15")
        return value


def puzzle_solvable(board: list[int]) -> bool:
    inversions = sum(1 for i in range(16) for j in range(i + 1, 16) if board[i] and board[j] and board[i] > board[j]); blank_row_from_bottom = 4 - board.index(0) // 4
    return (inversions + blank_row_from_bottom) % 2 == 1


class FifteenPuzzleEngine(AlgorithmEngine[PuzzleConfig]):
    algorithm_id = "astar-15-puzzle"
    goal = tuple(range(1, 16)) + (0,)

    def heuristic(self, state: tuple[int, ...]) -> int:
        return sum(abs(i // 4 - (value - 1) // 4) + abs(i % 4 - (value - 1) % 4) for i, value in enumerate(state) if value)

    def neighbours(self, state: tuple[int, ...]) -> list[tuple[tuple[int, ...], str]]:
        blank = state.index(0); row, col = divmod(blank, 4); moves = [("up", -1, 0), ("right", 0, 1), ("down", 1, 0), ("left", 0, -1)]; result = []
        for label, dr, dc in moves:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 4 and 0 <= nc < 4:
                target = nr * 4 + nc; board = list(state); board[blank], board[target] = board[target], board[blank]; result.append((tuple(board), label))
        return result

    def run(self) -> AlgorithmResult:
        start = tuple(self.config.board)
        self.record(AlgorithmEvent(iteration=0, event_type="INITIALIZED", state=list(start), metadata={"board": list(start), "goal": list(self.goal), "solvable": puzzle_solvable(list(start))}))
        if not puzzle_solvable(list(start)):
            self.record(AlgorithmEvent(iteration=1, event_type="FAILED", state=list(start), metadata={"message": "This puzzle is not solvable."})); return AlgorithmResult(algorithm_id=self.algorithm_id, status="failed", events=self.events, final_state=self.events[-1])
        queue = []; counter = count(); g = {start: 0}; parents: dict[tuple[int, ...], tuple[tuple[int, ...] | None, str | None]] = {start: (None, None)}; closed = set(); heapq.heappush(queue, (self.heuristic(start), 0, next(counter), start)); expanded = 0
        while queue and expanded < self.config.max_expansions:
            f, distance, _, state = heapq.heappop(queue)
            if state in closed: continue
            closed.add(state); expanded += 1; h = self.heuristic(state)
            if state == self.goal:
                moves = []; current = state
                while parents[current][0] is not None: parent, move = parents[current]; moves.append(move); current = parent  # type: ignore[assignment]
                moves.reverse(); metrics: dict[str, int | float | str | None] = {"nodes_expanded": expanded, "path_cost": len(moves), "path_length": len(moves)}; self.record(AlgorithmEvent(iteration=len(self.events), event_type="SOLUTION_FOUND", state=list(state), metrics=metrics, metadata={"moves": moves})); self.record(AlgorithmEvent(iteration=len(self.events), event_type="COMPLETED", state=list(state), metrics=metrics, metadata={"moves": moves})); return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])
            for candidate, move in self.neighbours(state):
                tentative = g[state] + 1
                if tentative < g.get(candidate, 1_000_000):
                    g[candidate] = tentative; parents[candidate] = (state, move); heapq.heappush(queue, (tentative + self.heuristic(candidate), tentative, next(counter), candidate))
            self.record(AlgorithmEvent(iteration=len(self.events), event_type="STATE_EVALUATED", state=list(state), metrics={"nodes_expanded": expanded, "g": float(distance), "h": float(h), "f": float(f)}, metadata={"open_size": len(queue)}))
        self.record(AlgorithmEvent(iteration=len(self.events), event_type="FAILED", metrics={"nodes_expanded": expanded}, metadata={"message": "Search limit reached."})); return AlgorithmResult(algorithm_id=self.algorithm_id, status="failed", events=self.events, final_state=self.events[-1])
