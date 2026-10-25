from __future__ import annotations

from typing import Literal, cast

from pydantic import BaseModel, Field, field_validator

from .astar_grid import AStarGridConfig, AStarGridEngine
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
    status: str
    path_cost: int | float | None
    path_length: int
    nodes_expanded: int
    nodes_generated: int
    event_count: int


class HeuristicComparisonEngine(AlgorithmEngine[HeuristicComparisonConfig]):
    """Orchestrate comparable A* runs without changing the A* implementation."""

    algorithm_id = "astar-heuristic-comparison"

    def run(self) -> AlgorithmResult:
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
                        "rows": self.config.grid.rows,
                        "cols": self.config.grid.cols,
                        "obstacles": sorted(self.config.grid.obstacles),
                    },
                    "heuristics": list(self.config.heuristics),
                    "start": self.config.grid.start,
                    "goal": self.config.grid.goal,
                },
            )
        )

        for index, heuristic in enumerate(self.config.heuristics, start=1):
            run_config = self.config.grid.model_copy(update={"heuristic": heuristic})
            result = AStarGridEngine(run_config).run()
            final = result.final_state
            path_cost_value = final.metrics.get("path_cost")
            path_cost = path_cost_value if isinstance(path_cost_value, (int, float)) else None
            expanded_value = final.metrics.get("nodes_expanded", 0)
            generated_value = final.metrics.get("nodes_generated", 0)
            summary = HeuristicComparisonSummary(
                heuristic=heuristic,
                status=result.status,
                path_cost=path_cost,
                path_length=len(final.path),
                nodes_expanded=int(expanded_value) if isinstance(expanded_value, (int, float)) else 0,
                nodes_generated=int(generated_value) if isinstance(generated_value, (int, float)) else 0,
                event_count=len(result.events),
            )
            summaries.append(summary)
            runs.append(summary.model_dump())
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
                    },
                    metadata={"heuristic": heuristic, "summary": summary.model_dump()},
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
                metadata={"runs": runs, "best_heuristic": best.heuristic if best is not None else None},
            )
        )
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])


def compare_heuristics(config: HeuristicComparisonConfig) -> list[HeuristicComparisonSummary]:
    """Return compact summaries while retaining the full event-oriented engine API."""
    result = HeuristicComparisonEngine(config).run()
    runs = cast(list[dict[str, object]], result.final_state.metadata["runs"])
    return [HeuristicComparisonSummary.model_validate(run) for run in runs]
