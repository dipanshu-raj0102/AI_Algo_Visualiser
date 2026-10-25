"""Reusable deterministic hill-climbing and simulated-annealing engines.

The engines in this module deliberately know nothing about a particular problem
domain.  A domain supplies an initial-state factory, an objective function, and
a neighbourhood function.  Every decision is represented as an
``AlgorithmEvent`` so executions can be replayed by the visualizer.
"""

from __future__ import annotations

import copy
import math
import random
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


StateT = TypeVar("StateT")
StateFactory = Callable[[random.Random, int], StateT]
NeighbourFactory = Callable[[StateT, random.Random], list[StateT]]
Objective = Callable[[StateT], float]
Serializer = Callable[[StateT], Any]


class LocalSearchConfig(BaseModel):
    """Shared controls for local-search algorithms."""

    max_iterations: int = Field(default=250, ge=1, le=100_000)
    restarts: int = Field(default=0, ge=0, le=1_000)
    seed: int = Field(default=482193, ge=0, le=2_147_483_647)
    maximize: bool = True


class HillClimbingConfig(LocalSearchConfig):
    """Configuration for steepest-ascent/descent hill climbing."""

    allow_sideways: bool = False
    max_sideways_moves: int = Field(default=0, ge=0, le=100_000)


class SimulatedAnnealingConfig(LocalSearchConfig):
    """Configuration for geometric-temperature simulated annealing."""

    initial_temperature: float = Field(default=10.0, gt=0)
    cooling_rate: float = Field(default=0.95, gt=0, lt=1)
    minimum_temperature: float = Field(default=0.001, gt=0)

    @field_validator("minimum_temperature")
    @classmethod
    def temperature_is_reachable(cls, value: float, info: Any) -> float:
        # The full cross-field relationship is checked by the run loop; this
        # validator only prevents a nonsensical non-positive temperature.
        return value


class _LocalSearchEngine(AlgorithmEngine[LocalSearchConfig], Generic[StateT]):
    """Common state/event plumbing for reusable local-search strategies."""

    algorithm_id = "local-search"

    def __init__(
        self,
        config: LocalSearchConfig,
        *,
        initial_state: StateFactory[StateT] | None = None,
        objective: Objective[StateT] | None = None,
        neighbours: NeighbourFactory[StateT] | None = None,
        neighbors: NeighbourFactory[StateT] | None = None,
        serializer: Serializer[StateT] | None = None,
    ) -> None:
        super().__init__(config)
        self._initial_state_factory = initial_state
        self._objective = objective
        self._neighbour_factory = neighbours or neighbors
        self._serializer = serializer or self._default_serializer
        self._event_iteration = 0

    @staticmethod
    def _default_serializer(state: StateT) -> Any:
        if isinstance(state, tuple):
            return [_LocalSearchEngine._default_serializer(item) for item in state]
        if isinstance(state, list):
            return [_LocalSearchEngine._default_serializer(item) for item in state]
        if isinstance(state, dict):
            return {str(key): _LocalSearchEngine._default_serializer(value) for key, value in state.items()}
        return state

    def _make_initial_state(self, rng: random.Random, restart: int) -> StateT:
        if self._initial_state_factory is not None:
            return copy.deepcopy(self._initial_state_factory(rng, restart))
        return copy.deepcopy(self.initial_state(rng, restart))

    def _score(self, state: StateT) -> float:
        if self._objective is not None:
            return float(self._objective(state))
        return float(self.objective(state))

    def _neighbours(self, state: StateT, rng: random.Random) -> list[StateT]:
        if self._neighbour_factory is not None:
            values = self._neighbour_factory(state, rng)
        else:
            values = self.neighbors(state, rng)
        return [copy.deepcopy(value) for value in values]

    def initial_state(self, rng: random.Random, restart: int = 0) -> StateT:
        raise NotImplementedError

    def objective(self, state: StateT) -> float:
        raise NotImplementedError

    def neighbours(self, state: StateT, rng: random.Random) -> list[StateT]:
        raise NotImplementedError

    def neighbors(self, state: StateT, rng: random.Random) -> list[StateT]:
        """American-spelling alias for domains that use ``neighbors``."""
        return self.neighbours(state, rng)

    def _is_better(self, left: float, right: float) -> bool:
        return left > right if self.config.maximize else left < right

    def _delta(self, candidate: float, current: float) -> float:
        return candidate - current if self.config.maximize else current - candidate

    def _metrics(
        self,
        *,
        current_score: float,
        best_score: float,
        optimization_iteration: int,
        candidate_evaluations: int,
        accepted_moves: int,
        rejected_moves: int,
        restarts: int,
        temperature: float | None = None,
    ) -> dict[str, int | float | str | None]:
        return {
            "optimization_iteration": optimization_iteration,
            "candidate_evaluations": candidate_evaluations,
            "accepted_moves": accepted_moves,
            "rejected_moves": rejected_moves,
            "restarts": restarts,
            "current_score": current_score,
            "best_score": best_score,
            "temperature": temperature,
        }

    def _record_search_event(
        self,
        event_type: str,
        *,
        state: StateT | None,
        metrics: dict[str, int | float | str | None],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._event_iteration += 1
        self.record(
            AlgorithmEvent(
                iteration=self._event_iteration,
                event_type=event_type,
                current_node=None,
                path=[],
                state=self._serializer(state) if state is not None else None,
                metrics=metrics,
                metadata={"state": self._serializer(state) if state is not None else None, **(metadata or {})},
            )
        )

    def _result(self, status: str = "completed") -> AlgorithmResult:
        return AlgorithmResult(
            algorithm_id=self.algorithm_id,
            status=status,
            events=self.events,
            final_state=self.events[-1],
        )


class HillClimbingEngine(_LocalSearchEngine[StateT], Generic[StateT]):
    """Steepest-improvement hill climbing with optional random restarts."""

    algorithm_id = "hill-climbing"

    config: LocalSearchConfig

    def __init__(self, config: LocalSearchConfig, **kwargs: Any) -> None:
        super().__init__(config, **kwargs)

    def run(self) -> AlgorithmResult:
        self.events = []
        self._event_iteration = -1
        rng = random.Random(self.config.seed)
        best_state: StateT | None = None
        best_score = -math.inf if self.config.maximize else math.inf
        candidate_evaluations = accepted_moves = rejected_moves = 0
        optimization_iteration = 0
        restart_count = 0
        sideways_moves = 0
        first_state = self._make_initial_state(rng, 0)
        first_score = self._score(first_state)
        best_state, best_score = first_state, first_score
        self._record_search_event(
            "INITIALIZED",
            state=first_state,
            metrics=self._metrics(
                current_score=first_score, best_score=best_score, optimization_iteration=0,
                candidate_evaluations=0, accepted_moves=0, rejected_moves=0, restarts=0,
            ),
            metadata={"seed": self.config.seed, "strategy": "hill-climbing", "restart": 0},
        )
        self._record_search_event(
            "BEST_SOLUTION",
            state=first_state,
            metrics=self._metrics(
                current_score=first_score, best_score=best_score, optimization_iteration=0,
                candidate_evaluations=0, accepted_moves=0, rejected_moves=0, restarts=0,
            ),
            metadata={"score": best_score, "reason": "initial-state"},
        )

        for restart in range(self.config.restarts + 1):
            if restart > 0:
                restart_count += 1
                current = self._make_initial_state(rng, restart)
                current_score = self._score(current)
                sideways_moves = 0
                self._record_search_event(
                    "RESTART",
                    state=current,
                    metrics=self._metrics(
                        current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                        candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                        rejected_moves=rejected_moves, restarts=restart_count,
                    ),
                    metadata={"restart": restart, "seed_stream_position": restart},
                )
            else:
                current, current_score = first_state, first_score

            for _ in range(self.config.max_iterations):
                optimization_iteration += 1
                candidates = self._neighbours(current, rng)
                if not candidates:
                    self._record_search_event(
                        "LOCAL_OPTIMUM", state=current,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count,
                        ),
                        metadata={"reason": "empty-neighbourhood"},
                    )
                    break

                scored: list[tuple[float, StateT, int]] = []
                for index, candidate in enumerate(candidates):
                    score = self._score(candidate)
                    candidate_evaluations += 1
                    scored.append((score, candidate, index))
                    self._record_search_event(
                        "CANDIDATE_EVALUATED", state=candidate,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count,
                        ),
                        metadata={"candidate": self._serializer(candidate), "candidate_score": score,
                                  "current_score": current_score, "delta": self._delta(score, current_score),
                                  "candidate_index": index},
                    )
                if self.config.maximize:
                    candidate_score, candidate, candidate_index = max(scored, key=lambda item: item[0])
                else:
                    candidate_score, candidate, candidate_index = min(scored, key=lambda item: item[0])

                improves = self._is_better(candidate_score, current_score)
                sideways = (
                    candidate_score == current_score
                    and getattr(self.config, "allow_sideways", False)
                    and sideways_moves < getattr(self.config, "max_sideways_moves", 0)
                )
                if not improves and not sideways:
                    rejected_moves += 1
                    self._record_search_event(
                        "MOVE_REJECTED", state=current,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count,
                        ),
                        metadata={"candidate": self._serializer(candidate), "candidate_score": candidate_score,
                                  "delta": self._delta(candidate_score, current_score), "candidate_index": candidate_index},
                    )
                    self._record_search_event(
                        "LOCAL_OPTIMUM", state=current,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count,
                        ),
                        metadata={"reason": "no-improving-neighbour"},
                    )
                    break

                if sideways:
                    sideways_moves += 1
                else:
                    sideways_moves = 0
                move_delta = self._delta(candidate_score, current_score)
                accepted_moves += 1
                current, current_score = candidate, candidate_score
                self._record_search_event(
                    "MOVE_ACCEPTED", state=current,
                    metrics=self._metrics(
                        current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                        candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                        rejected_moves=rejected_moves, restarts=restart_count,
                    ),
                    metadata={"candidate": self._serializer(candidate), "candidate_score": candidate_score,
                              "delta": move_delta, "candidate_index": candidate_index,
                              "sideways": sideways},
                )
                if self._is_better(current_score, best_score):
                    best_state, best_score = copy.deepcopy(current), current_score
                    self._record_search_event(
                        "BEST_SOLUTION", state=best_state,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count,
                        ),
                        metadata={"score": best_score, "reason": "accepted-improvement"},
                    )

        assert best_state is not None
        self._record_search_event(
            "COMPLETED", state=best_state,
            metrics=self._metrics(
                current_score=self._score(best_state), best_score=best_score, optimization_iteration=optimization_iteration,
                candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                rejected_moves=rejected_moves, restarts=restart_count,
            ),
            metadata={"best_solution": self._serializer(best_state), "best_score": best_score},
        )
        return self._result()


class SimulatedAnnealingEngine(_LocalSearchEngine[StateT], Generic[StateT]):
    """Metropolis simulated annealing with seeded acceptance decisions."""

    algorithm_id = "simulated-annealing"

    config: LocalSearchConfig

    def __init__(self, config: LocalSearchConfig, **kwargs: Any) -> None:
        super().__init__(config, **kwargs)

    def run(self) -> AlgorithmResult:
        self.events = []
        self._event_iteration = -1
        rng = random.Random(self.config.seed)
        best_state: StateT | None = None
        best_score = -math.inf if self.config.maximize else math.inf
        candidate_evaluations = accepted_moves = rejected_moves = 0
        optimization_iteration = 0
        restart_count = 0
        initial_temperature = getattr(self.config, "initial_temperature", 10.0)
        temperature = initial_temperature
        first_state = self._make_initial_state(rng, 0)
        first_score = self._score(first_state)
        best_state, best_score = first_state, first_score
        self._record_search_event(
            "INITIALIZED", state=first_state,
            metrics=self._metrics(
                current_score=first_score, best_score=best_score, optimization_iteration=0,
                candidate_evaluations=0, accepted_moves=0, rejected_moves=0, restarts=0,
                temperature=initial_temperature,
            ),
            metadata={"seed": self.config.seed, "strategy": "simulated-annealing", "initial_temperature": initial_temperature},
        )
        self._record_search_event(
            "BEST_SOLUTION", state=first_state,
            metrics=self._metrics(
                current_score=first_score, best_score=best_score, optimization_iteration=0,
                candidate_evaluations=0, accepted_moves=0, rejected_moves=0, restarts=0,
                temperature=initial_temperature,
            ),
            metadata={"score": best_score, "reason": "initial-state"},
        )

        for restart in range(self.config.restarts + 1):
            if restart > 0:
                restart_count += 1
                current = self._make_initial_state(rng, restart)
                current_score = self._score(current)
                temperature = initial_temperature
                self._record_search_event(
                    "RESTART", state=current,
                    metrics=self._metrics(
                        current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                        candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                        rejected_moves=rejected_moves, restarts=restart_count, temperature=temperature,
                    ),
                    metadata={"restart": restart, "temperature_reset": temperature},
                )
            else:
                current, current_score = first_state, first_score
                temperature = initial_temperature

            for _ in range(self.config.max_iterations):
                minimum_temperature = getattr(self.config, "minimum_temperature", 0.001)
                cooling_rate = getattr(self.config, "cooling_rate", 0.95)
                if temperature <= minimum_temperature:
                    break
                optimization_iteration += 1
                candidates = self._neighbours(current, rng)
                if not candidates:
                    self._record_search_event(
                        "LOCAL_OPTIMUM", state=current,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count, temperature=temperature,
                        ),
                        metadata={"reason": "empty-neighbourhood"},
                    )
                    break

                candidate = candidates[rng.randrange(len(candidates))]
                candidate_score = self._score(candidate)
                candidate_evaluations += 1
                delta = self._delta(candidate_score, current_score)
                probability = 1.0 if delta >= 0 else math.exp(max(-745.0, delta / temperature))
                draw = rng.random()
                self._record_search_event(
                    "CANDIDATE_EVALUATED", state=candidate,
                    metrics=self._metrics(
                        current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                        candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                        rejected_moves=rejected_moves, restarts=restart_count, temperature=temperature,
                    ),
                    metadata={"candidate": self._serializer(candidate), "candidate_score": candidate_score,
                              "current_score": current_score, "delta": delta, "temperature": temperature,
                              "acceptance_probability": probability, "random_draw": draw},
                )
                accepted = delta >= 0 or draw < probability
                if accepted:
                    accepted_moves += 1
                    current, current_score = candidate, candidate_score
                    self._record_search_event(
                        "MOVE_ACCEPTED", state=current,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count, temperature=temperature,
                        ),
                        metadata={"candidate": self._serializer(candidate), "candidate_score": candidate_score,
                                  "delta": delta, "temperature": temperature, "probabilistic": delta < 0},
                    )
                    if self._is_better(current_score, best_score):
                        best_state, best_score = copy.deepcopy(current), current_score
                        self._record_search_event(
                            "BEST_SOLUTION", state=best_state,
                            metrics=self._metrics(
                                current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                                candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                                rejected_moves=rejected_moves, restarts=restart_count, temperature=temperature,
                            ),
                            metadata={"score": best_score, "reason": "accepted-improvement", "temperature": temperature},
                        )
                else:
                    rejected_moves += 1
                    self._record_search_event(
                        "MOVE_REJECTED", state=current,
                        metrics=self._metrics(
                            current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                            candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                            rejected_moves=rejected_moves, restarts=restart_count, temperature=temperature,
                        ),
                        metadata={"candidate": self._serializer(candidate), "candidate_score": candidate_score,
                                  "delta": delta, "temperature": temperature, "acceptance_probability": probability,
                                  "random_draw": draw},
                    )
                next_temperature = max(minimum_temperature, temperature * cooling_rate)
                self._record_search_event(
                    "TEMPERATURE_UPDATED", state=current,
                    metrics=self._metrics(
                        current_score=current_score, best_score=best_score, optimization_iteration=optimization_iteration,
                        candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                        rejected_moves=rejected_moves, restarts=restart_count, temperature=next_temperature,
                    ),
                    metadata={"previous_temperature": temperature, "temperature": next_temperature,
                              "cooling_rate": cooling_rate},
                )
                temperature = next_temperature

        assert best_state is not None
        self._record_search_event(
            "COMPLETED", state=best_state,
            metrics=self._metrics(
                current_score=self._score(best_state), best_score=best_score, optimization_iteration=optimization_iteration,
                candidate_evaluations=candidate_evaluations, accepted_moves=accepted_moves,
                rejected_moves=rejected_moves, restarts=restart_count, temperature=temperature,
            ),
            metadata={"best_solution": self._serializer(best_state), "best_score": best_score, "temperature": temperature},
        )
        return self._result()


__all__ = [
    "HillClimbingConfig",
    "HillClimbingEngine",
    "LocalSearchConfig",
    "SimulatedAnnealingConfig",
    "SimulatedAnnealingEngine",
]
