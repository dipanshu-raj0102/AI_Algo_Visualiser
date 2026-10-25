from __future__ import annotations

import hashlib
import json
from typing import Literal, cast

from pydantic import BaseModel, Field, field_validator

from .astar_grid import HEURISTIC_DEFINITIONS, AStarGridConfig, AStarGridEngine, generate_obstacles
from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


HeuristicName = Literal["manhattan", "euclidean", "chebyshev", "zero"]


class HeuristicComparisonConfig(BaseModel):
    """Run the existing A* engine with a deterministic set of heuristics."""

    grid: AStarGridConfig = Field(default_factory=AStarGridConfig)
    heuristics: list[HeuristicName] = Field(default_factory=lambda: ["manhattan", "euclidean", "chebyshev", "zero"], min_length=1, max_length=4)

    @field_validator("heuristics")
    @classmethod
    def reject_duplicate_heuristics(cls, value: list[HeuristicName]) -> list[HeuristicName]:
        if len(set(value)) != len(value):
            raise ValueError("heuristics must not contain duplicates")
        return value


class HeuristicComparisonSummary(BaseModel):
    heuristic: HeuristicName
    heuristic_formula: str
    heuristic_description: str
    status: str
    path_cost: int | float | None
    path_length: int
    nodes_expanded: int
    nodes_generated: int
    expanded: int
    discovered: int
    max_frontier: int
    explored_cells: int
    execution_time: float
    reached: bool
    steps: int
    event_count: int


class HeuristicComparisonEngine(AlgorithmEngine[HeuristicComparisonConfig]):
    """Orchestrate comparable A* runs without changing the A* implementation."""

    algorithm_id = "astar-heuristic-comparison"

    def _shared_grid(self) -> AStarGridConfig:
        """Materialize one problem once; every heuristic receives this exact config."""
        grid = self.config.grid
        obstacles = grid.obstacles or generate_obstacles(grid)
        return grid.model_copy(update={"obstacles": sorted(set(obstacles))})

    @staticmethod
    def _problem_metadata(grid: AStarGridConfig) -> dict[str, object]:
        payload = {
            "rows": grid.rows,
            "cols": grid.cols,
            "start": grid.start,
            "goal": grid.goal,
            "obstacles": sorted(grid.obstacles),
            "obstacle_density": grid.obstacle_density,
            "movement_model": grid.movement_model,
            "seed": grid.seed,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return {"signature": hashlib.sha256(encoded).hexdigest()[:16], **payload}

    def run(self) -> AlgorithmResult:
        self.reset()
        shared_grid = self._shared_grid()
        problem = self._problem_metadata(shared_grid)
        summaries: list[HeuristicComparisonSummary] = []
        runs: list[dict[str, object]] = []
        paths: list[list[str]] = []
        self.record(
            AlgorithmEvent(
                iteration=0,
                event_type="INITIALIZED",
                current_node=self.config.grid.start,
                metadata={
                    "grid": {
                        "rows": shared_grid.rows,
                        "cols": shared_grid.cols,
                        "obstacles": sorted(shared_grid.obstacles),
                    },
                    "heuristics": list(self.config.heuristics),
                    "start": shared_grid.start,
                    "goal": shared_grid.goal,
                    "problem": problem,
                },
            )
        )

        for index, heuristic in enumerate(self.config.heuristics, start=1):
            run_config = shared_grid.model_copy(update={"heuristic": heuristic})
            result = AStarGridEngine(run_config).run()
            final = result.final_state
            trace = [event.model_dump() for event in result.events]
            path_cost_value = final.metrics.get("path_cost")
            path_cost = path_cost_value if isinstance(path_cost_value, (int, float)) else None
            expanded_value = final.metrics.get("nodes_expanded", 0)
            generated_value = final.metrics.get("nodes_generated", 0)
            max_frontier_value = final.metrics.get("max_frontier_size", 0)
            explored_cells_value = final.metrics.get("explored_cells", len(final.explored))
            execution_time_value = final.metrics.get("execution_time", 0.0)
            reached_value = final.metrics.get("reached", result.status == "completed")
            steps_value = final.metrics.get("steps", len(result.events))
            summary = HeuristicComparisonSummary(
                heuristic=heuristic,
                heuristic_formula=HEURISTIC_DEFINITIONS[heuristic]["formula"],
                heuristic_description=HEURISTIC_DEFINITIONS[heuristic]["description"],
                status=result.status,
                path_cost=path_cost,
                path_length=len(final.path),
                nodes_expanded=int(expanded_value) if isinstance(expanded_value, (int, float)) else 0,
                nodes_generated=int(generated_value) if isinstance(generated_value, (int, float)) else 0,
                expanded=int(expanded_value) if isinstance(expanded_value, (int, float)) else 0,
                discovered=int(generated_value) if isinstance(generated_value, (int, float)) else 0,
                max_frontier=int(max_frontier_value) if isinstance(max_frontier_value, (int, float)) else 0,
                explored_cells=int(explored_cells_value) if isinstance(explored_cells_value, (int, float)) else len(final.explored),
                execution_time=float(execution_time_value) if isinstance(execution_time_value, (int, float)) else 0.0,
                reached=bool(reached_value),
                steps=int(steps_value) if isinstance(steps_value, (int, float)) else len(result.events),
                event_count=len(result.events),
            )
            summaries.append(summary)
            runs.append({
                **summary.model_dump(),
                "problem": problem,
                "trace": trace,
                # `events` is the explicit replay payload used by generic clients.
                "events": trace,
            })
            paths.append(list(final.path))
            self.record(
                AlgorithmEvent(
                    iteration=index,
                    event_type="HEURISTIC_COMPLETED",
                    current_node=final.current_node,
                    frontier=final.frontier,
                    explored=final.explored,
                    path=final.path,
                    metrics={
                        "run_index": index,
                        "nodes_expanded": summary.nodes_expanded,
                        "nodes_generated": summary.nodes_generated,
                        "path_cost": summary.path_cost,
                        "path_length": summary.path_length,
                        "expanded": summary.expanded,
                        "discovered": summary.discovered,
                        "max_frontier": summary.max_frontier,
                        "explored_cells": summary.explored_cells,
                        "execution_time": summary.execution_time,
                        "reached": summary.reached,
                        "steps": summary.steps,
                    },
                    metadata={"heuristic": heuristic, "summary": summary.model_dump(), "problem": problem, "trace": trace, "events": trace},
                )
            )

        completed = [(index, summary) for index, summary in enumerate(summaries) if summary.status == "completed"]
        best_index, best = min(
            completed,
            key=lambda item: (float(item[1].path_cost or float("inf")), item[1].nodes_expanded),
            default=(-1, None),
        )
        final_metrics: dict[str, int | float | str | None] = {
            "runs": len(summaries),
            "completed_runs": len(completed),
            "reached_runs": sum(1 for summary in summaries if summary.reached),
            "total_nodes_expanded": sum(summary.nodes_expanded for summary in summaries),
            "best_path_cost": best.path_cost if best is not None else None,
        }
        self.record(
            AlgorithmEvent(
                iteration=len(summaries) + 1,
                event_type="COMPLETED",
                current_node=self.config.grid.goal if completed else None,
                path=paths[best_index] if best is not None else [],
                metrics=final_metrics,
                metadata={"runs": runs, "best_heuristic": best.heuristic if best is not None else None, "problem": problem},
            )
        )
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])


def compare_heuristics(config: HeuristicComparisonConfig) -> list[HeuristicComparisonSummary]:
    """Return compact summaries while retaining the full event-oriented engine API."""
    result = HeuristicComparisonEngine(config).run()
    runs = cast(list[dict[str, object]], result.final_state.metadata["runs"])
    return [HeuristicComparisonSummary.model_validate(run) for run in runs]
