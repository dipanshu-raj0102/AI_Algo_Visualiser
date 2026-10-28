# API endpoints

FastAPI publishes interactive documentation at `/api/docs` and ReDoc at `/api/redoc`.

## Core endpoints

- `GET /api/v1/health` — liveness check.
- `GET /api/v1/algorithms` — registry metadata used by the library.
- `GET /api/v1/algorithms/{algorithm_id}` — one algorithm definition.
- `POST /api/v1/executions` — validate a configuration, execute the backend engine, and return replayable events.
- `GET /api/v1/executions/{execution_id}` — retrieve an in-memory execution.
- `GET /api/v1/executions/{execution_id}/export?format=json|csv` — export an execution trace.
- `POST /api/v1/comparisons` — execute compatible registered algorithms against one shared configuration.
- `GET /api/v1/comparisons/{comparison_id}` — retrieve a comparison result.

Executions are currently process-local and intentionally bounded by each algorithm's configuration model. PostgreSQL persistence and streaming can be added without changing the event payload contract.

## A* heuristic comparison payload

`POST /api/v1/executions` accepts the registered comparison identifier with a nested configuration:

```json
{
  "algorithm_id": "astar-heuristic-comparison",
  "config": {
    "grid": {
      "rows": 14,
      "cols": 22,
      "start": "1,1",
      "goal": "12,20",
      "obstacle_density": 0.18,
      "seed": 482193,
      "movement_model": "4-way"
    },
    "heuristics": ["manhattan", "euclidean", "chebyshev", "zero"]
  }
}
```

The response uses the normal `ExecutionResponse` envelope. Its terminal event stores `metadata.runs`, one item per heuristic. Every item contains:

- `problem.signature`, rows, columns, start, goal, normalized obstacles, seed, `movement_model`, and `cost_model`;
- the stable heuristic identifier, name, formula, description, assumptions, and suitability text;
- `status`, `reached`, `path_cost`, `path_length`, `expanded`, `discovered`, `max_frontier`, `explored_cells`, `steps`, `event_count`, and measured `execution_time`;
- `events` (also available as `trace`), using the standard `AlgorithmEvent` fields.

`AlgorithmEvent` snapshots expose `current_node`, `frontier`, `explored`, `path`, `metrics`, and `metadata`. `FAILED` with `reached: false` represents a valid no-path execution; HTTP/configuration failures remain separate 4xx responses. Runtime is wall-clock data and must not be used for structural determinism assertions.

The comparison currently supports four-way movement and unit orthogonal edge costs only. Invalid heuristic names, duplicate heuristics, unsupported movement models, malformed coordinates, out-of-bounds points, and obstacle endpoints are rejected by Pydantic validation and return HTTP 422 from the execution route.
