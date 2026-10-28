# Architecture overview

## Vertical slice

The application is built around a replayable execution log rather than UI-owned algorithm logic:

```text
Validated config
      ↓
Algorithm registry → engine factory → AlgorithmEvent[]
      ↓                                  ↓
 FastAPI REST                         React playback
      ↓                                  ↓
 execution history                 reusable visualizers + metrics
```

The backend is the source of truth for algorithm state. Each engine emits structured events containing frontier, explored nodes, current node, reconstructed path, metrics, and educational metadata. The frontend only renders and replays those events.

## Heuristic comparison vertical slice

`astar-heuristic-comparison` is an orchestration engine, not a second A* implementation. It materializes one `AStarGridConfig` problem, including generated obstacles, before invoking the authoritative `AStarGridEngine` once for each selected heuristic. Every run carries the same `problem.signature`, dimensions, endpoints, obstacle list, `movement_model`, `cost_model`, and seed. The current comparison model is four-way movement with unit cost for each orthogonal move.

The comparison result stores compact run summaries and full nested replay events in `final_state.metadata.runs`. Each run includes its heuristic definition, real metrics, status, and `events`/`trace`. Structural traces are deterministic for the same validated config; wall-clock `execution_time` is intentionally variable.

## Replay lifecycle

`frontend/src/hooks/useAnimationController.ts` is the shared playback authority for the comparison workspace and the generic visualizer. It owns one cursor and one timeout at a time. Pause, restart, seek, speed changes, replacement event lists, completion, and unmount invalidate the previous generation before a new timeout can advance the cursor. `eventAt()` pins a shorter comparison trace to its final event while the shared cursor continues through longer traces.

Controls are state transitions over the returned event list: play/resume, pause, restart, step forward, step backward, seek, fast-forward at 8×, finish, and bounded speed selection. The frontend never recomputes A* decisions.

## Adding an algorithm

1. Add a Pydantic configuration model.
2. Implement an `AlgorithmEngine` with a deterministic `run()` method and `AlgorithmEvent` snapshots.
3. Add metadata and a factory to `backend/app/algorithms/registry.py`.
4. Add API and correctness tests.
5. Add a visualization adapter or reuse an existing one in the frontend.

## Current scope and deliberate gaps

The initial slice stores executions in process memory and returns a complete event log in one REST response. This keeps the first flow deterministic and easy to test. Durable persistence and SSE/WebSocket streaming can be layered on the same event contract after the core visualizer patterns are proven.

The current application also includes Greedy Best-First, A* vs Greedy comparison, weighted terrain, and the A* heuristic impact analysis. The transport remains synchronous and process-local: complete event logs are returned in REST responses. Durable persistence and streaming can be layered on the same event contract after payload-size limits are measured.
