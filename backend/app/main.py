from __future__ import annotations

import csv
import io
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .algorithms.registry import REGISTRY, list_metadata
from .schemas import ComparisonRequest, ComparisonResponse, ExecutionRequest, ExecutionResponse

app = FastAPI(title="AI Algorithm Visualizer API", version="0.1.0", docs_url="/api/docs", redoc_url="/api/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

EXECUTIONS: dict[str, ExecutionResponse] = {}
COMPARISONS: dict[str, ComparisonResponse] = {}


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "algorithm-engine"}


@app.get("/api/v1/algorithms", description="List all registered algorithm modules and their visualization metadata.")
def algorithms() -> list[dict[str, object]]:
    return list_metadata()


@app.get("/api/v1/algorithms/{algorithm_id}")
def algorithm(algorithm_id: str) -> dict[str, object]:
    definition = REGISTRY.get(algorithm_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    return next(item for item in list_metadata() if item["id"] == algorithm_id)


def _prepare_config(request_algorithm_id: str, raw_config: dict[str, object]):
    definition = REGISTRY[request_algorithm_id]
    config = definition.config_model.model_validate(raw_config)
    if request_algorithm_id in {"astar-grid", "greedy-best-first-grid"} and not config.obstacles:
        from .algorithms.astar_grid import generate_obstacles

        config.obstacles = generate_obstacles(config)
    if request_algorithm_id == "weighted-astar-grid" and not config.terrain:
        from .algorithms.weighted_astar_grid import generate_terrain

        config.terrain = generate_terrain(config)
    if request_algorithm_id == "astar-heuristic-comparison" and not config.grid.obstacles:
        from .algorithms.astar_grid import generate_obstacles

        config.grid.obstacles = generate_obstacles(config.grid)
    return config


def _execute(algorithm_id: str, raw_config: dict[str, object]) -> ExecutionResponse:
    definition = REGISTRY[algorithm_id]
    config = _prepare_config(algorithm_id, raw_config)
    result = definition.engine_factory(config).run()
    execution_id = str(uuid4())
    response = ExecutionResponse(execution_id=execution_id, algorithm_id=result.algorithm_id, status=result.status, events=[event.model_dump() for event in result.events], final_state=result.final_state.model_dump())
    EXECUTIONS[execution_id] = response
    return response


@app.post("/api/v1/executions", response_model=ExecutionResponse, description="Run one registered algorithm and return its replayable event trace.")
def create_execution(request: ExecutionRequest) -> ExecutionResponse:
    definition = REGISTRY.get(request.algorithm_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    try:
        return _execute(request.algorithm_id, request.config)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/comparisons", response_model=ComparisonResponse, description="Run compatible registered algorithms against the same configuration.")
def create_comparison(request: ComparisonRequest) -> ComparisonResponse:
    unknown = [algorithm_id for algorithm_id in request.algorithm_ids if algorithm_id not in REGISTRY]
    if unknown:
        raise HTTPException(status_code=404, detail=f"Unknown algorithms: {', '.join(unknown)}")
    try:
        comparison_config = request.config
        if set(request.algorithm_ids).issubset({"astar-grid", "greedy-best-first-grid"}):
            base_config = REGISTRY[request.algorithm_ids[0]].config_model.model_validate(request.config)
            if not base_config.obstacles:
                from .algorithms.astar_grid import generate_obstacles

                base_config.obstacles = generate_obstacles(base_config)
            comparison_config = base_config.model_dump()
        results = [_execute(algorithm_id, comparison_config) for algorithm_id in request.algorithm_ids]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    comparison_id = str(uuid4())
    summaries = [{"algorithm_id": result.algorithm_id, "status": result.status, "path_cost": result.final_state.get("metrics", {}).get("path_cost"), "path_length": len(result.final_state.get("path", [])), "events": len(result.events), "metrics": result.final_state.get("metrics", {})} for result in results]
    response = ComparisonResponse(comparison_id=comparison_id, results=results, summary={"algorithms": summaries})
    COMPARISONS[comparison_id] = response
    return response


@app.get("/api/v1/comparisons/{comparison_id}", response_model=ComparisonResponse)
def get_comparison(comparison_id: str) -> ComparisonResponse:
    comparison = COMPARISONS.get(comparison_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comparison


@app.get("/api/v1/executions/{execution_id}/export")
def export_execution(execution_id: str, format: str = "json"):
    execution = get_execution(execution_id)
    if format == "json":
        return execution
    if format != "csv":
        raise HTTPException(status_code=400, detail="format must be json or csv")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["iteration", "event_type", "current_node", "nodes_expanded", "path_cost", "frontier_size"])
    for event in execution.events:
        writer.writerow([event.get("iteration"), event.get("event_type"), event.get("current_node"), event.get("metrics", {}).get("nodes_expanded"), event.get("metrics", {}).get("path_cost"), len(event.get("frontier", []))])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={execution_id}.csv"})


@app.get("/api/v1/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: str) -> ExecutionResponse:
    execution = EXECUTIONS.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
