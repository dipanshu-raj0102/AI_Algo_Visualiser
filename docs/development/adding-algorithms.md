# Adding an algorithm

1. Define a Pydantic configuration model with limits and seed controls where randomness is used.
2. Implement `AlgorithmEngine[Config]` in `backend/app/algorithms/`.
3. Emit `AlgorithmEvent` snapshots from the real state transitions. Use `metadata` for domain-specific values and `explanation` for educational copy.
4. Return `AlgorithmResult` with `completed` or `failed` status and a final event.
5. Register the configuration model, engine factory, category, and visualization type in `registry.py`.
6. Add correctness, edge-case, reproducibility, metrics, and event-order tests.
7. Reuse the frontend registry/library and add a visualization adapter only when the existing generic state view is not sufficient.

The frontend should replay backend events. It must not duplicate algorithm logic.

## Adding a heuristic to the A* comparison

1. Add the stable identifier and its `name`, `formula`, `description`, `assumptions`, and `suitability` text to `HEURISTIC_DEFINITIONS` in `backend/app/algorithms/astar_grid.py`.
2. Extend the `AStarGridConfig` validator and the `HeuristicName` literal in `heuristic_comparison.py`.
3. Keep the search loop in `AStarGridEngine`; `HeuristicComparisonEngine` should only create a copy of the shared validated grid with the new heuristic.
4. Add tests for the heuristic value, shared-problem identity, deterministic structural events, path/metric behavior, and invalid configuration.
5. Update the frontend `HeuristicName`, display order, and formula fallback only if the backend metadata cannot be used during a loading/error state.

## How visualizers consume replay events

The generic visualizer and comparison page use `useAnimationController` over the returned `events` array. Components render the active `AlgorithmEvent`; they do not run search logic. Grid adapters read `frontier`, `explored`, `path`, `current_node`, and `metadata.grid`. Other algorithm adapters use `state`, `candidate`, and domain-specific metadata. New controls should call the shared controller rather than creating their own interval or timeout.

The controller's `seek`, step, restart, and finish actions pause automatic playback. One generation token invalidates stale callbacks after pause, restart, speed changes, replacement execution, completion, and unmount. Comparison consumers may use `eventAt` to pin a shorter run to its final event while a shared cursor advances.

## Current movement and cost limitations

The A* grid comparison is intentionally limited to `movement_model = "4-way"` and unit cost for each orthogonal move. The zero heuristic is therefore documented as Dijkstra/uniform-cost search for this exact model. Do not generalize heuristic suitability or optimality claims to diagonal movement, terrain weights, or other cost functions without extending the validated config and the engine's neighbor/cost model first.
