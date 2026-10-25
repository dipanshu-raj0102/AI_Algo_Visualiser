from __future__ import annotations

import heapq
import math
import random
from itertools import count

from pydantic import BaseModel, Field, field_validator, model_validator

from .astar_grid import node_key, parse_node
from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


class WeightedAStarGridConfig(BaseModel):
    """Configuration for A* where moving into a cell has a positive terrain cost."""

    rows: int = Field(default=14, ge=4, le=40)
    cols: int = Field(default=22, ge=4, le=60)
    start: str = "1,1"
    goal: str = "12,20"
    obstacles: list[str] = Field(default_factory=list)
    terrain: dict[str, float] = Field(default_factory=dict)
    terrain_min: float = Field(default=1, gt=0, le=100)
    terrain_max: float = Field(default=9, gt=0, le=100)
    heuristic: str = "manhattan"
    seed: int = Field(default=482193, ge=0, le=2_147_483_647)

    @field_validator("heuristic")
    @classmethod
    def validate_heuristic(cls, value: str) -> str:
        if value not in {"manhattan", "euclidean"}:
            raise ValueError("heuristic must be manhattan or euclidean")
        return value

    @model_validator(mode="after")
    def validate_points_and_terrain(self) -> "WeightedAStarGridConfig":
        if self.terrain_min > self.terrain_max:
            raise ValueError("terrain_min must not exceed terrain_max")
        start = parse_node(self.start)
        goal = parse_node(self.goal)
        for label, point in (("start", start), ("goal", goal)):
            if not (0 <= point[0] < self.rows and 0 <= point[1] < self.cols):
                raise ValueError(f"{label} must be inside the grid")
        if start == goal:
            raise ValueError("start and goal must be different")
        obstacle_set = set(self.obstacles)
        if self.start in obstacle_set or self.goal in obstacle_set:
            raise ValueError("start and goal cannot be obstacles")
        for obstacle in self.obstacles:
            row, col = parse_node(obstacle)
            if not (0 <= row < self.rows and 0 <= col < self.cols):
                raise ValueError("obstacles must be inside the grid")
        for terrain_node, terrain_cost in self.terrain.items():
            row, col = parse_node(terrain_node)
            if not (0 <= row < self.rows and 0 <= col < self.cols):
                raise ValueError("terrain nodes must be inside the grid")
            if terrain_node in obstacle_set:
                raise ValueError("terrain cannot be assigned to an obstacle")
            if not math.isfinite(terrain_cost) or not self.terrain_min <= terrain_cost <= self.terrain_max:
                raise ValueError("terrain costs must be finite and within terrain_min and terrain_max")
        return self


def generate_terrain(config: WeightedAStarGridConfig) -> dict[str, float]:
    """Generate a deterministic terrain map for every traversable cell."""
    rng = random.Random(config.seed)
    terrain = dict(config.terrain)
    for row in range(config.rows):
        for col in range(config.cols):
            key = node_key((row, col))
            if key in config.obstacles or key in terrain:
                continue
            terrain[key] = round(rng.uniform(config.terrain_min, config.terrain_max), 3)
    return dict(sorted(terrain.items()))


class WeightedAStarGridEngine(AlgorithmEngine[WeightedAStarGridConfig]):
    """Optimal A* for positive terrain costs, ordered with deterministic tie-breaking."""

    algorithm_id = "weighted-astar-grid"

    def __init__(self, config: WeightedAStarGridConfig) -> None:
        super().__init__(config)
        self.obstacles = set(config.obstacles)
        self.start = config.start
        self.goal = config.goal
        self.terrain = dict(config.terrain)
        self.minimum_cost = min(self.terrain.values(), default=config.terrain_min)
        self.minimum_cost = min(self.minimum_cost, config.terrain_min)

    def cost(self, node: str) -> float:
        return self.terrain.get(node, self.config.terrain_min)

    def heuristic(self, node: str) -> float:
        row, col = parse_node(node)
        goal_row, goal_col = parse_node(self.goal)
        if self.config.heuristic == "euclidean":
            distance = math.hypot(goal_row - row, goal_col - col)
        else:
            distance = abs(goal_row - row) + abs(goal_col - col)
        return distance * self.minimum_cost

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
            for node, values in sorted(frontier.items(), key=lambda item: (item[1][0], item[1][1], item[0]))
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
        queue: list[tuple[float, float, int, str]] = []
        counter = count()
        start_h = self.heuristic(self.start)
        frontier[self.start] = (start_h, 0.0, start_h)
        heapq.heappush(queue, (start_h, 0.0, next(counter), self.start))
        expanded = 0
        generated = 1
        max_frontier_size = 1
        iteration = 0
        metrics = {
            "nodes_expanded": expanded,
            "nodes_generated": generated,
            "path_cost": None,
            "max_frontier_size": max_frontier_size,
        }
        self.snapshot(
            iteration,
            "INITIALIZED",
            self.start,
            frontier,
            explored,
            [],
            metrics,
            {
                "grid": {"rows": self.config.rows, "cols": self.config.cols, "obstacles": sorted(self.obstacles)},
                "terrain": dict(sorted(self.terrain.items())),
                "start": self.start,
                "goal": self.goal,
                "heuristic": self.config.heuristic,
                "minimum_terrain_cost": self.minimum_cost,
                "seed": self.config.seed,
            },
        )

        while queue:
            queued_f, queued_g, _, current = heapq.heappop(queue)
            current_entry = frontier.get(current)
            if current_entry is None or queued_f != current_entry[0] or queued_g != current_entry[1]:
                continue
            del frontier[current]
            iteration += 1
            expanded += 1
            explored.add(current)
            path = self.reconstruct(parents, current)
            metrics = {
                "nodes_expanded": expanded,
                "nodes_generated": generated,
                "path_cost": None,
                "max_frontier_size": max_frontier_size,
            }
            self.snapshot(iteration, "NODE_EXPANDED", current, frontier, explored, path, metrics)

            if current == self.goal:
                metrics["path_cost"] = g_score[current]
                self.snapshot(
                    iteration + 1,
                    "SOLUTION_FOUND",
                    current,
                    frontier,
                    explored,
                    path,
                    metrics,
                    {"message": "A* reached the goal with minimum accumulated terrain cost."},
                )
                self.snapshot(iteration + 2, "COMPLETED", current, frontier, explored, path, metrics)
                return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])

            for neighbour in self.neighbours(current):
                if neighbour in explored:
                    continue
                tentative_g = g_score[current] + self.cost(neighbour)
                if tentative_g >= g_score.get(neighbour, math.inf):
                    continue
                parents[neighbour] = current
                g_score[neighbour] = tentative_g
                h = self.heuristic(neighbour)
                f = tentative_g + h
                was_known = neighbour in frontier
                frontier[neighbour] = (f, tentative_g, h)
                heapq.heappush(queue, (f, tentative_g, next(counter), neighbour))
                if not was_known:
                    generated += 1
                max_frontier_size = max(max_frontier_size, len(frontier))
                iteration += 1
                metrics = {
                    "nodes_expanded": expanded,
                    "nodes_generated": generated,
                    "path_cost": None,
                    "max_frontier_size": max_frontier_size,
                }
                self.snapshot(
                    iteration,
                    "NODE_UPDATED" if was_known else "NODE_DISCOVERED",
                    current,
                    frontier,
                    explored,
                    self.reconstruct(parents, current),
                    metrics,
                    {
                        "candidate": neighbour,
                        "terrain_cost": self.cost(neighbour),
                        "g": round(tentative_g, 3),
                        "h": round(h, 3),
                        "f": round(f, 3),
                    },
                )

        metrics = {
            "nodes_expanded": expanded,
            "nodes_generated": generated,
            "path_cost": None,
            "max_frontier_size": max_frontier_size,
        }
        self.snapshot(iteration + 1, "FAILED", None, frontier, explored, [], metrics, {"message": "No route exists for this terrain layout."})
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="failed", events=self.events, final_state=self.events[-1])

    @staticmethod
    def reconstruct(parents: dict[str, str | None], node: str) -> list[str]:
        path: list[str] = []
        current: str | None = node
        while current is not None:
            path.append(current)
            current = parents.get(current)
        return list(reversed(path))
