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

## Adding an algorithm

1. Add a Pydantic configuration model.
2. Implement an `AlgorithmEngine` with a deterministic `run()` method and `AlgorithmEvent` snapshots.
3. Add metadata and a factory to `backend/app/algorithms/registry.py`.
4. Add API and correctness tests.
5. Add a visualization adapter or reuse an existing one in the frontend.

## Current scope and deliberate gaps

The initial slice stores executions in process memory and returns a complete event log in one REST response. This keeps the first flow deterministic and easy to test. Durable persistence and SSE/WebSocket streaming can be layered on the same event contract after the core visualizer patterns are proven.

The next planned vertical slices are Greedy Best-First, A* vs Greedy comparison, weighted terrain, and heuristic impact analysis.
