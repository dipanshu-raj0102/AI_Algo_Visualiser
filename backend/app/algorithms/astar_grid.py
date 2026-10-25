from __future__ import annotations

import heapq
import math
import random
from itertools import count

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


class AStarGridConfig(BaseModel):
    rows: int = Field(default=14, ge=4, le=40)
    cols: int = Field(default=22, ge=4, le=60)
    start: str = "1,1"
    goal: str = "12,20"
    obstacles: list[str] = Field(default_factory=list)
    obstacle_density: float = Field(default=0.18, ge=0, le=0.45)
    heuristic: str = "manhattan"
    seed: int = Field(default=482193, ge=0, le=2_147_483_647)

    @field_validator("heuristic")
    @classmethod
    def validate_heuristic(cls, value: str) -> str:
        if value not in {"manhattan", "euclidean", "chebyshev", "zero"}:
            raise ValueError("heuristic must be manhattan, euclidean, chebyshev, or zero")
        return value

    @model_validator(mode="after")
    def validate_points(self) -> "AStarGridConfig":
        start = parse_node(self.start)
        goal = parse_node(self.goal)
        for label, point in (("start", start), ("goal", goal)):
            if not (0 <= point[0] < self.rows and 0 <= point[1] < self.cols):
                raise ValueError(f"{label} must be inside the grid")
        if start == goal:
            raise ValueError("start and goal must be different")
        if self.start in self.obstacles or self.goal in self.obstacles:
            raise ValueError("start and goal cannot be obstacles")
        for obstacle in self.obstacles:
            row, col = parse_node(obstacle)
            if not (0 <= row < self.rows and 0 <= col < self.cols):
                raise ValueError("obstacles must be inside the grid")
        return self


def parse_node(value: str) -> tuple[int, int]:
    try:
        row, col = (int(part.strip()) for part in value.split(","))
    except (TypeError, ValueError) as exc:
        raise ValueError("nodes must use the 'row,col' format") from exc
    return row, col


def node_key(node: tuple[int, int]) -> str:
    return f"{node[0]},{node[1]}"


def generate_obstacles(config: AStarGridConfig) -> list[str]:
    """Generate a reproducible obstacle field while preserving a viable corridor."""
    rng = random.Random(config.seed)
    start = parse_node(config.start)
    goal = parse_node(config.goal)
    obstacles = set(config.obstacles)
    for row in range(config.rows):
        for col in range(config.cols):
            key = node_key((row, col))
            if (row, col) in {start, goal} or key in obstacles:
                continue
            if rng.random() < config.obstacle_density:
                obstacles.add(key)
    # Keep a monotone corridor open so the default demo is always solvable.
    row, col = start
    while row != goal[0]:
        row += 1 if goal[0] > row else -1
        obstacles.discard(node_key((row, col)))
    while col != goal[1]:
        col += 1 if goal[1] > col else -1
        obstacles.discard(node_key((row, col)))
    return sorted(obstacles)


class AStarGridEngine(AlgorithmEngine[AStarGridConfig]):
    algorithm_id = "astar-grid"

    def __init__(self, config: AStarGridConfig) -> None:
        super().__init__(config)
        self.obstacles = set(config.obstacles)
        self.start = config.start
        self.goal = config.goal

    def heuristic(self, node: str) -> float:
        row, col = parse_node(node)
        goal_row, goal_col = parse_node(self.goal)
        if self.config.heuristic == "zero":
            return 0.0
        if self.config.heuristic == "euclidean":
            return math.hypot(goal_row - row, goal_col - col)
        if self.config.heuristic == "chebyshev":
            return max(abs(goal_row - row), abs(goal_col - col))
        return abs(goal_row - row) + abs(goal_col - col)

    def neighbours(self, node: str) -> list[str]:
        row, col = parse_node(node)
        candidates = [(row - 1, col), (row, col + 1), (row + 1, col), (row, col - 1)]
        return [
            node_key(point)
            for point in candidates
            if 0 <= point[0] < self.config.rows
            and 0 <= point[1] < self.config.cols
            and node_key(point) not in self.obstacles
        ]

    def snapshot(
        self,
        iteration: int,
        event_type: str,
        current_node: str | None,
        frontier: dict[str, tuple[float, float, float]],
        explored: set[str],
        path: list[str],
        metrics: dict[str, int | float | str | None],
        metadata: dict[str, object] | None = None,
    ) -> None:
        frontier_items = [
            {"node": node, "g": round(values[1], 3), "h": round(values[2], 3), "f": round(values[0], 3)}
            for node, values in sorted(frontier.items(), key=lambda item: (item[1][0], item[0]))
        ]
        self.record(
            AlgorithmEvent(
                iteration=iteration,
                event_type=event_type,
                current_node=current_node,
                frontier=frontier_items,
                explored=sorted(explored),
                path=path,
                metrics=metrics,
                metadata=metadata or {},
            )
        )

    def run(self) -> AlgorithmResult:
        frontier: dict[str, tuple[float, float, float]] = {}
        parents: dict[str, str | None] = {self.start: None}
        g_score = {self.start: 0.0}
        explored: set[str] = set()
        queue: list[tuple[float, int, str]] = []
        counter = count()
        start_h = self.heuristic(self.start)
        frontier[self.start] = (start_h, 0.0, start_h)
        heapq.heappush(queue, (start_h, next(counter), self.start))
        expanded = 0
        generated = 1
        max_frontier_size = 1
        iteration = 0
        base_metrics = {"nodes_expanded": expanded, "nodes_generated": generated, "path_cost": None, "max_frontier_size": max_frontier_size}
        self.snapshot(iteration, "INITIALIZED", self.start, frontier, explored, [], base_metrics, {"grid": {"rows": self.config.rows, "cols": self.config.cols, "obstacles": sorted(self.obstacles)}, "start": self.start, "goal": self.goal, "heuristic": self.config.heuristic, "seed": self.config.seed})

        while queue:
            _, _, current = heapq.heappop(queue)
            if current not in frontier:
                continue
            del frontier[current]
            iteration += 1
            expanded += 1
            explored.add(current)
            path = self.reconstruct(parents, current)
            metrics = {"nodes_expanded": expanded, "nodes_generated": generated, "path_cost": None, "max_frontier_size": max_frontier_size}
            self.snapshot(iteration, "NODE_EXPANDED", current, frontier, explored, path, metrics)

            if current == self.goal:
                cost = g_score[current]
                metrics["path_cost"] = cost
                self.snapshot(iteration + 1, "SOLUTION_FOUND", current, frontier, explored, path, metrics, {"message": "The goal has the lowest available f(n) and the reconstructed route is optimal for this grid."})
                self.snapshot(iteration + 2, "COMPLETED", current, frontier, explored, path, metrics)
                return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])

            for neighbour in self.neighbours(current):
                if neighbour in explored:
                    continue
                tentative_g = g_score[current] + 1
                if tentative_g >= g_score.get(neighbour, math.inf):
                    continue
                parents[neighbour] = current
                g_score[neighbour] = tentative_g
                h = self.heuristic(neighbour)
                f = tentative_g + h
                was_known = neighbour in frontier
                frontier[neighbour] = (f, tentative_g, h)
                heapq.heappush(queue, (f, next(counter), neighbour))
                generated += 1 if not was_known else 0
                max_frontier_size = max(max_frontier_size, len(frontier))
                iteration += 1
                metrics = {"nodes_expanded": expanded, "nodes_generated": generated, "path_cost": None, "max_frontier_size": max_frontier_size}
                self.snapshot(iteration, "NODE_UPDATED" if was_known else "NODE_DISCOVERED", current, frontier, explored, self.reconstruct(parents, current), metrics, {"candidate": neighbour, "g": tentative_g, "h": round(h, 3), "f": round(f, 3)})

        metrics = {"nodes_expanded": expanded, "nodes_generated": generated, "path_cost": None, "max_frontier_size": max_frontier_size}
        self.snapshot(iteration + 1, "FAILED", None, frontier, explored, [], metrics, {"message": "No route exists for this obstacle layout."})
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="failed", events=self.events, final_state=self.events[-1])

    @staticmethod
    def reconstruct(parents: dict[str, str | None], node: str) -> list[str]:
        path: list[str] = []
        current: str | None = node
        while current is not None:
            path.append(current)
            current = parents.get(current)
        return list(reversed(path))
