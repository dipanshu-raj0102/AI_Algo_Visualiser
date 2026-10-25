"""Hill-climbing and simulated-annealing engines for N-Queens."""

from __future__ import annotations

import random

from pydantic import Field, field_validator

from .local_search import HillClimbingEngine, LocalSearchConfig, SimulatedAnnealingEngine


class NQueensConfig(LocalSearchConfig):
    n: int = Field(default=8, ge=4, le=80)
    initial_board: list[int] | None = None
    allow_sideways: bool = False
    max_sideways_moves: int = Field(default=0, ge=0, le=100_000)
    initial_temperature: float = Field(default=8.0, gt=0)
    cooling_rate: float = Field(default=0.96, gt=0, lt=1)
    minimum_temperature: float = Field(default=0.001, gt=0)

    @field_validator("initial_board")
    @classmethod
    def validate_board(cls, value: list[int] | None) -> list[int] | None:
        if value is not None and any(not isinstance(column, int) for column in value):
            raise ValueError("initial_board entries must be integers")
        return value


def queen_conflicts(board: tuple[int, ...] | list[int]) -> int:
    """Count attacking queen pairs (zero means a valid solution)."""
    conflicts = 0
    for row, column in enumerate(board):
        for other_row in range(row + 1, len(board)):
            other_column = board[other_row]
            if column == other_column or abs(column - other_column) == other_row - row:
                conflicts += 1
    return conflicts


class NQueensHillClimbingEngine(HillClimbingEngine[tuple[int, ...]]):
    algorithm_id = "n-queens-hill-climbing"

    def __init__(self, config: NQueensConfig) -> None:
        super().__init__(config)

    @property
    def queens_config(self) -> NQueensConfig:
        return self.config  # type: ignore[return-value]

    def initial_state(self, rng: random.Random, restart: int = 0) -> tuple[int, ...]:
        if restart == 0 and self.queens_config.initial_board is not None:
            board = tuple(self.queens_config.initial_board)
            if len(board) != self.queens_config.n or any(not 0 <= column < self.queens_config.n for column in board):
                raise ValueError("initial_board must contain n columns in the board bounds")
            return board
        board = list(range(self.queens_config.n))
        rng.shuffle(board)
        return tuple(board)

    def objective(self, state: tuple[int, ...]) -> float:
        return -float(queen_conflicts(state))

    def neighbours(self, state: tuple[int, ...], rng: random.Random) -> list[tuple[int, ...]]:
        result: list[tuple[int, ...]] = []
        for row in range(self.queens_config.n):
            for column in range(self.queens_config.n):
                if column == state[row]:
                    continue
                candidate = list(state)
                candidate[row] = column
                result.append(tuple(candidate))
        return result


class NQueensSimulatedAnnealingEngine(SimulatedAnnealingEngine[tuple[int, ...]]):
    algorithm_id = "n-queens-simulated-annealing"

    def __init__(self, config: NQueensConfig) -> None:
        super().__init__(config)

    @property
    def queens_config(self) -> NQueensConfig:
        return self.config  # type: ignore[return-value]

    def initial_state(self, rng: random.Random, restart: int = 0) -> tuple[int, ...]:
        if restart == 0 and self.queens_config.initial_board is not None:
            board = tuple(self.queens_config.initial_board)
            if len(board) != self.queens_config.n or any(not 0 <= column < self.queens_config.n for column in board):
                raise ValueError("initial_board must contain n columns in the board bounds")
            return board
        board = list(range(self.queens_config.n))
        rng.shuffle(board)
        return tuple(board)

    def objective(self, state: tuple[int, ...]) -> float:
        return -float(queen_conflicts(state))

    def neighbours(self, state: tuple[int, ...], rng: random.Random) -> list[tuple[int, ...]]:
        row = rng.randrange(self.queens_config.n)
        columns = [column for column in range(self.queens_config.n) if column != state[row]]
        return [tuple((*state[:row], column, *state[row + 1 :])) for column in columns]


NQueensEngine = NQueensHillClimbingEngine

__all__ = [
    "NQueensConfig",
    "NQueensEngine",
    "NQueensHillClimbingEngine",
    "NQueensSimulatedAnnealingEngine",
    "queen_conflicts",
]
