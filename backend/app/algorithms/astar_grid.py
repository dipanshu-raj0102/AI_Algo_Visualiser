from __future__ import annotations

import heapq
import math
import random
import time
from itertools import count

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


HEURISTIC_DEFINITIONS: dict[str, dict[str, str]] = {
    "manhattan": {"formula": "|dr| + |dc|", "description": "Sum of orthogonal distance to the goal."},
    "euclidean": {"formula": "sqrt(dr² + dc²)", "description": "Straight-line distance to the goal."},
    "chebyshev": {"formula": "max(|dr|, |dc|)", "description": "Maximum coordinate distance to the goal."},
    "zero": {"formula": "0", "description": "No heuristic; A* becomes Dijkstra / uniform-cost search."},
}


class AStarGridConfig(BaseModel):
    rows: int = Field(default=14, ge=4, le=40)
    cols: int = Field(default=22, ge=4, le=60)
    start: str = "1,1"
    goal: str = "12,20"
    obstacles: list[str] = Field(default_factory=list)
    obstacle_density: float = Field(default=0.18, ge=0, le=0.45)
    heuristic: str = "manhattan"
    movement_model: str = "4-way"
    seed: int = Field(default=482193, ge=0, le=2_147_483_647)

    @field_validator("heuristic")
    @classmethod
    def validate_heuristic(cls, value: str) -> str:
        if value not in {"manhattan", "euclidean", "chebyshev", "zero"}:
            raise ValueError("heuristic must be manhattan, euclidean, chebyshev, or zero")
        return value

    @field_validator("movement_model")
    @classmethod
    def validate_movement_model(cls, value: str) -> str:
        if value != "4-way":
            raise ValueError("movement_model must be 4-way")
        return value

    @model_validator(mode="after")
    def validate_points(self) -> "AStarGridConfig":
        start = parse_node(self.start)
        goal = parse_node(self.goal)
        for label, point in (("start", start), ("goal", goal)):
            if not (0 <= point[0] < self.rows and 0 <= point[1] < self.cols):
                raise ValueError(f"{label} must be inside the grid")
        normalized_obstacles = {node_key(parse_node(obstacle)) for obstacle in self.obstacles}
        self.start = node_key(start)
        self.goal = node_key(goal)
        self.obstacles = sorted(normalized_obstacles)
        if self.start in normalized_obstacles or self.goal in normalized_obstacles:
            raise ValueError("start and goal cannot be obstacles")
        for row, col in (parse_node(obstacle) for obstacle in normalized_obstacles):
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

    @staticmethod
    def _metrics(
        *,
        expanded: int,
        discovered: int,
        max_frontier: int,
        path: list[str],
        explored: set[str],
        reached: bool,
        steps: int,
        execution_time: float = 0.0,
    ) -> dict[str, int | float | str | None]:
        """Return the stable metric vocabulary shared by the comparison UI and API."""
        path_cost: float | None = float(len(path) - 1) if reached else None
        path_length = len(path) if reached else 0
        return {
            # Canonical comparison metrics.
            "expanded": expanded,
            "discovered": discovered,
            "max_frontier": max_frontier,
            "path_length": path_length,
            "path_cost": path_cost,
            "explored_cells": len(explored),
            "execution_time": execution_time,
            "reached": reached,
            "steps": steps,
            # Backwards-compatible names used by the existing grid visualizer.
            "nodes_expanded": expanded,
            "nodes_generated": discovered,
            "max_frontier_size": max_frontier,
        }

    def _problem_metadata(self) -> dict[str, object]:
        heuristic_details = HEURISTIC_DEFINITIONS[self.config.heuristic]
        return {
            "grid": {"rows": self.config.rows, "cols": self.config.cols, "obstacles": sorted(self.obstacles)},
            "start": self.start,
            "goal": self.goal,
            "seed": self.config.seed,
            "obstacle_density": self.config.obstacle_density,
            "movement_model": self.config.movement_model,
            "heuristic": self.config.heuristic,
            "heuristic_formula": heuristic_details["formula"],
            "heuristic_description": heuristic_details["description"],
            "cost_model": "unit cost for each orthogonal move",
            "execution_time_unit": "milliseconds",
            "metric_formulas": {
                "expanded": "count of nodes removed from the frontier and evaluated",
                "discovered": "count of unique nodes first admitted to the frontier",
                "max_frontier": "maximum number of unique pending nodes",
                "path_length": "number of cells in the reconstructed path, including endpoints",
                "path_cost": "sum of unit orthogonal move costs",
                "explored_cells": "count of evaluated cells",
                "steps": "replay iteration of the emitted state transition",
            },
        }

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        # Keep the public metric useful for very fast toy grids while retaining
        # the measured wall-clock duration at millisecond precision.
        return max(round((time.perf_counter() - started_at) * 1000, 3), 0.001)

    def run(self) -> AlgorithmResult:
        self.reset()
        started_at = time.perf_counter()
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
        base_metrics = self._metrics(expanded=expanded, discovered=generated, max_frontier=max_frontier_size, path=[], explored=explored, reached=False, steps=iteration)
        self.snapshot(iteration, "INITIALIZED", self.start, frontier, explored, [], base_metrics, self._problem_metadata())

        if self.start == self.goal:
            explored.add(self.start)
            path = [self.start]
            metrics = self._metrics(expanded=1, discovered=1, max_frontier=1, path=path, explored=explored, reached=True, steps=2, execution_time=self._elapsed_ms(started_at))
            metrics["path_cost"] = 0.0
            self.snapshot(1, "SOLUTION_FOUND", self.start, {}, explored, path, metrics, {"message": "The start is already the goal, so the optimal path has zero movement cost."})
            self.snapshot(2, "COMPLETED", self.start, {}, explored, path, metrics)
            return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])

        while queue:
            _, _, current = heapq.heappop(queue)
            if current not in frontier:
                continue
            del frontier[current]
            iteration += 1
            expanded += 1
            explored.add(current)
            path = self.reconstruct(parents, current)
            metrics = self._metrics(expanded=expanded, discovered=generated, max_frontier=max_frontier_size, path=path, explored=explored, reached=False, steps=iteration)
            self.snapshot(iteration, "NODE_EXPANDED", current, frontier, explored, path, metrics)

            if current == self.goal:
                cost = g_score[current]
                metrics = self._metrics(expanded=expanded, discovered=generated, max_frontier=max_frontier_size, path=path, explored=explored, reached=True, steps=iteration + 1)
                metrics["path_cost"] = cost
                self.snapshot(iteration + 1, "SOLUTION_FOUND", current, frontier, explored, path, metrics, {"message": "The goal has the lowest available f(n) and the reconstructed route is optimal for this grid."})
                metrics = dict(metrics)
                metrics["steps"] = iteration + 2
                self.snapshot(iteration + 2, "COMPLETED", current, frontier, explored, path, metrics)
                self.events[-1].metrics["execution_time"] = self._elapsed_ms(started_at)
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
                metrics = self._metrics(expanded=expanded, discovered=generated, max_frontier=max_frontier_size, path=self.reconstruct(parents, current), explored=explored, reached=False, steps=iteration)
                self.snapshot(iteration, "NODE_UPDATED" if was_known else "NODE_DISCOVERED", current, frontier, explored, self.reconstruct(parents, current), metrics, {"candidate": neighbour, "g": tentative_g, "h": round(h, 3), "f": round(f, 3)})

        metrics = self._metrics(expanded=expanded, discovered=generated, max_frontier=max_frontier_size, path=[], explored=explored, reached=False, steps=iteration + 1)
        self.snapshot(iteration + 1, "FAILED", None, frontier, explored, [], metrics, {"message": "No route exists for this obstacle layout."})
        self.events[-1].metrics["execution_time"] = self._elapsed_ms(started_at)
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="failed", events=self.events, final_state=self.events[-1])

    @staticmethod
    def reconstruct(parents: dict[str, str | None], node: str) -> list[str]:
        path: list[str] = []
        current: str | None = node
        while current is not None:
            path.append(current)
            current = parents.get(current)
        return list(reversed(path))
