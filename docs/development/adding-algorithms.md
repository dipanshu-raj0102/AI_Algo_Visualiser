# Adding an algorithm

1. Define a Pydantic configuration model with limits and seed controls where randomness is used.
2. Implement `AlgorithmEngine[Config]` in `backend/app/algorithms/`.
3. Emit `AlgorithmEvent` snapshots from the real state transitions. Use `metadata` for domain-specific values and `explanation` for educational copy.
4. Return `AlgorithmResult` with `completed` or `failed` status and a final event.
5. Register the configuration model, engine factory, category, and visualization type in `registry.py`.
6. Add correctness, edge-case, reproducibility, metrics, and event-order tests.
7. Reuse the frontend registry/library and add a visualization adapter only when the existing generic state view is not sufficient.

The frontend should replay backend events. It must not duplicate algorithm logic.
