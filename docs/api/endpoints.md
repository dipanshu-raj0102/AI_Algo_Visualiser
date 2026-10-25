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
