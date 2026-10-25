"""One-dimensional function-landscape local-search demonstrations."""

from __future__ import annotations

import math
import random
from typing import cast

from pydantic import Field, model_validator

from .local_search import HillClimbingEngine, LocalSearchConfig, SimulatedAnnealingEngine


class FunctionLandscapeConfig(LocalSearchConfig):
    """Configuration shared by the function-landscape hill climber."""

    function_name: str = "peaks"
    lower_bound: float = Field(default=-6.0)
    upper_bound: float = Field(default=6.0)
    step_size: float = Field(default=0.25, gt=0)
    initial_x: float | None = None
    target: float = 1.5
    allow_sideways: bool = False
    max_sideways_moves: int = Field(default=0, ge=0, le=100_000)
    initial_temperature: float = Field(default=10.0, gt=0)
    cooling_rate: float = Field(default=0.95, gt=0, lt=1)
    minimum_temperature: float = Field(default=0.001, gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "FunctionLandscapeConfig":
        if self.lower_bound >= self.upper_bound:
            raise ValueError("lower_bound must be less than upper_bound")
        if self.initial_x is not None and not self.lower_bound <= self.initial_x <= self.upper_bound:
            raise ValueError("initial_x must be inside the landscape bounds")
        if self.function_name not in {"peaks", "quadratic", "sinusoidal"}:
            raise ValueError("function_name must be peaks, quadratic, or sinusoidal")
        return self


class FunctionLandscapeHillClimbingEngine(HillClimbingEngine[float]):
    algorithm_id = "function-landscape-hill-climbing"

    def __init__(self, config: FunctionLandscapeConfig) -> None:
        super().__init__(config)

    @property
    def landscape_config(self) -> FunctionLandscapeConfig:
        return cast(FunctionLandscapeConfig, self.config)

    def initial_state(self, rng: random.Random, restart: int = 0) -> float:
        config = self.landscape_config
        if restart == 0 and config.initial_x is not None:
            return config.initial_x
        return rng.uniform(config.lower_bound, config.upper_bound)

    def objective(self, state: float) -> float:
        config = self.landscape_config
        if config.function_name == "quadratic":
            return -(state - config.target) ** 2
        if config.function_name == "sinusoidal":
            return math.sin(state) + 0.25 * math.sin(3 * state)
        return math.sin(2.2 * state) + 0.45 * math.cos(4.7 * state) - 0.025 * state * state

    def neighbours(self, state: float, rng: random.Random) -> list[float]:
        config = self.landscape_config
        return [
            candidate
            for candidate in (state - config.step_size, state + config.step_size)
            if config.lower_bound <= candidate <= config.upper_bound
        ]


class FunctionLandscapeSimulatedAnnealingEngine(SimulatedAnnealingEngine[float]):
    algorithm_id = "function-landscape-simulated-annealing"

    def __init__(self, config: FunctionLandscapeConfig) -> None:
        super().__init__(config)

    @property
    def landscape_config(self) -> FunctionLandscapeConfig:
        return cast(FunctionLandscapeConfig, self.config)

    def initial_state(self, rng: random.Random, restart: int = 0) -> float:
        config = self.landscape_config
        if restart == 0 and config.initial_x is not None:
            return config.initial_x
        return rng.uniform(config.lower_bound, config.upper_bound)

    def objective(self, state: float) -> float:
        config = self.landscape_config
        if config.function_name == "quadratic":
            return -(state - config.target) ** 2
        if config.function_name == "sinusoidal":
            return math.sin(state) + 0.25 * math.sin(3 * state)
        return math.sin(2.2 * state) + 0.45 * math.cos(4.7 * state) - 0.025 * state * state

    def neighbours(self, state: float, rng: random.Random) -> list[float]:
        config = self.landscape_config
        return [
            candidate
            for candidate in (state - config.step_size, state + config.step_size)
            if config.lower_bound <= candidate <= config.upper_bound
        ]


# The default engine is useful for callers that want the canonical hill-climb.
FunctionLandscapeEngine = FunctionLandscapeHillClimbingEngine

__all__ = [
    "FunctionLandscapeConfig",
    "FunctionLandscapeEngine",
    "FunctionLandscapeHillClimbingEngine",
    "FunctionLandscapeSimulatedAnnealingEngine",
]
