from __future__ import annotations

import random

from pydantic import Field

from .local_search import SimulatedAnnealingConfig, SimulatedAnnealingEngine


class SchedulingConfig(SimulatedAnnealingConfig):
    jobs: int = Field(default=4, ge=2, le=12)
    machines: int = Field(default=3, ge=1, le=8)
    slots: int = Field(default=12, ge=4, le=48)
    max_iterations: int = Field(default=200, ge=1, le=10_000)
    seed: int = Field(default=482193, ge=0, le=2_147_483_647)
    initial_temperature: float = Field(default=20, gt=0)
    cooling_rate: float = Field(default=.96, gt=0, lt=1)
    minimum_temperature: float = Field(default=.01, gt=0)
    restarts: int = Field(default=0, ge=0, le=20)
    maximize: bool = True


def schedule_cost(state: tuple[tuple[int, int], ...], config: SchedulingConfig) -> float:
    conflicts = 0
    for i, (machine, slot) in enumerate(state):
        if not 0 <= slot < config.slots or not 0 <= machine < config.machines: conflicts += 10
        for other_machine, other_slot in state[i + 1 :]:
            if machine == other_machine and slot == other_slot: conflicts += 12
    makespan = max((slot for _, slot in state), default=0) + 1
    return conflicts * 100 + makespan


class SchedulingAnnealingEngine(SimulatedAnnealingEngine[tuple[tuple[int, int], ...]]):
    algorithm_id = "simulated-annealing-scheduling"

    def __init__(self, config: SchedulingConfig) -> None:
        super().__init__(config)

    @property
    def schedule_config(self) -> SchedulingConfig:
        return self.config  # type: ignore[return-value]

    def initial_state(self, rng: random.Random, restart: int = 0) -> tuple[tuple[int, int], ...]:
        config = self.schedule_config
        return tuple((rng.randrange(config.machines), rng.randrange(config.slots)) for _ in range(config.jobs))

    def objective(self, state: tuple[tuple[int, int], ...]) -> float:
        return -schedule_cost(state, self.schedule_config)

    def neighbours(self, state: tuple[tuple[int, int], ...], rng: random.Random) -> list[tuple[tuple[int, int], ...]]:
        config = self.schedule_config
        result = []
        for _ in range(min(8, config.jobs * 2)):
            index = rng.randrange(config.jobs); candidate = list(state); candidate[index] = (rng.randrange(config.machines), rng.randrange(config.slots)); result.append(tuple(candidate))
        return result
