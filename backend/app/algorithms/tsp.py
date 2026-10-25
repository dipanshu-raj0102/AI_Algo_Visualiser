"""Deterministic local-search engines for the travelling-salesperson problem."""

from __future__ import annotations

import math
import random
from typing import Sequence

from pydantic import Field, field_validator

from .local_search import HillClimbingEngine, LocalSearchConfig, SimulatedAnnealingEngine


class TSPConfig(LocalSearchConfig):
    num_cities: int = Field(default=10, ge=3, le=100)
    cities: list[tuple[float, float]] = Field(default_factory=list)
    initial_tour: list[int] | None = None
    allow_sideways: bool = False
    max_sideways_moves: int = Field(default=0, ge=0, le=100_000)
    initial_temperature: float = Field(default=25.0, gt=0)
    cooling_rate: float = Field(default=0.97, gt=0, lt=1)
    minimum_temperature: float = Field(default=0.001, gt=0)

    @field_validator("cities")
    @classmethod
    def validate_cities(cls, value: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if value and len(value) < 3:
            raise ValueError("cities must contain at least three points")
        return value


def tour_distance(tour: Sequence[int], cities: Sequence[tuple[float, float]]) -> float:
    if len(tour) < 2:
        return 0.0
    return sum(
        math.dist(cities[tour[index]], cities[tour[(index + 1) % len(tour)]])
        for index in range(len(tour))
    )


def generate_cities(config: TSPConfig) -> list[tuple[float, float]]:
    """Generate a reproducible Euclidean instance when coordinates are omitted."""
    if config.cities:
        return [(float(point[0]), float(point[1])) for point in config.cities]
    rng = random.Random(config.seed)
    return [(round(rng.uniform(0, 100), 6), round(rng.uniform(0, 100), 6)) for _ in range(config.num_cities)]


class _TSPBase:
    @property
    def tsp_config(self) -> TSPConfig:
        return self.config  # type: ignore[return-value]

    @property
    def city_coordinates(self) -> list[tuple[float, float]]:
        if not hasattr(self, "_cities"):
            self._cities = generate_cities(self.tsp_config)
        return self._cities

    def initial_state(self, rng: random.Random, restart: int = 0) -> tuple[int, ...]:
        config = self.tsp_config
        city_count = len(self.city_coordinates)
        if restart == 0 and config.initial_tour is not None:
            tour = tuple(config.initial_tour)
            if len(tour) != city_count or set(tour) != set(range(city_count)):
                raise ValueError("initial_tour must be a permutation of all city indices")
            return tour
        tour = list(range(city_count))
        rng.shuffle(tour)
        return tuple(tour)

    def objective(self, state: tuple[int, ...]) -> float:
        return -tour_distance(state, self.city_coordinates)

    def neighbours(self, state: tuple[int, ...], rng: random.Random) -> list[tuple[int, ...]]:
        city_count = len(state)
        result: list[tuple[int, ...]] = []
        for left in range(city_count - 1):
            for right in range(left + 1, city_count):
                candidate = list(state)
                candidate[left], candidate[right] = candidate[right], candidate[left]
                result.append(tuple(candidate))
        return result


class TSPHillClimbingEngine(_TSPBase, HillClimbingEngine[tuple[int, ...]]):
    algorithm_id = "tsp-hill-climbing"

    def __init__(self, config: TSPConfig) -> None:
        super().__init__(config)


class TSPSimulatedAnnealingEngine(_TSPBase, SimulatedAnnealingEngine[tuple[int, ...]]):
    algorithm_id = "tsp-simulated-annealing"

    def __init__(self, config: TSPConfig) -> None:
        super().__init__(config)


TSPEngine = TSPHillClimbingEngine

__all__ = [
    "TSPConfig",
    "TSPEngine",
    "TSPHillClimbingEngine",
    "TSPSimulatedAnnealingEngine",
    "generate_cities",
    "tour_distance",
]
