from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .algorithms.registry import REGISTRY, list_metadata
from .schemas import ExecutionRequest, ExecutionResponse

app = FastAPI(title="AI Algorithm Visualizer API", version="0.1.0", docs_url="/api/docs", redoc_url="/api/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

EXECUTIONS: dict[str, ExecutionResponse] = {}


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "algorithm-engine"}


@app.get("/api/v1/algorithms")
def algorithms() -> list[dict[str, object]]:
    return list_metadata()


@app.get("/api/v1/algorithms/{algorithm_id}")
def algorithm(algorithm_id: str) -> dict[str, object]:
    definition = REGISTRY.get(algorithm_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    return next(item for item in list_metadata() if item["id"] == algorithm_id)


@app.post("/api/v1/executions", response_model=ExecutionResponse)
def create_execution(request: ExecutionRequest) -> ExecutionResponse:
    definition = REGISTRY.get(request.algorithm_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    try:
        config = definition.config_model.model_validate(request.config)
        if request.algorithm_id == "astar-grid" and not config.obstacles:
            from .algorithms.astar_grid import generate_obstacles

            config.obstacles = generate_obstacles(config)
        result = definition.engine_factory(config).run()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    execution_id = str(uuid4())
    response = ExecutionResponse(
        execution_id=execution_id,
        algorithm_id=result.algorithm_id,
        status=result.status,
        events=[event.model_dump() for event in result.events],
        final_state=result.final_state.model_dump(),
    )
    EXECUTIONS[execution_id] = response
    return response


@app.get("/api/v1/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: str) -> ExecutionResponse:
    execution = EXECUTIONS.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
