"""Tic-Tac-Toe minimax/alpha-beta visualisation engine."""

from __future__ import annotations

from itertools import combinations

from pydantic import BaseModel, Field, field_validator

from .game_search import GameAdapter, GameSearchEngine


class TicTacToeConfig(BaseModel):
    board: list[str] = Field(default_factory=lambda: [""] * 9)
    player: str = "X"
    max_depth: int = Field(default=9, ge=0, le=9)
    alpha_beta: bool = True

    @field_validator("player")
    @classmethod
    def validate_player(cls, value: str) -> str:
        if value not in {"X", "O"}:
            raise ValueError("player must be X or O")
        return value

    @field_validator("board")
    @classmethod
    def validate_board(cls, value: list[str]) -> list[str]:
        if len(value) != 9:
            raise ValueError("Tic-Tac-Toe board must contain 9 cells")
        if any(cell not in {"", ".", "X", "O"} for cell in value):
            raise ValueError("board cells must be empty, X, or O")
        return ["" if cell == "." else cell for cell in value]


class TicTacToeGame(GameAdapter[tuple[str, ...], int]):
    wins = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))

    def legal_moves(self, state: tuple[str, ...]) -> list[int]:
        return [index for index, cell in enumerate(state) if not cell]

    def apply_move(self, state: tuple[str, ...], move: int, player: str) -> tuple[str, ...]:
        board = list(state)
        board[move] = player
        return tuple(board)

    def terminal(self, state: tuple[str, ...]) -> str | None:
        for a, b, c in self.wins:
            if state[a] and state[a] == state[b] == state[c]:
                return state[a]
        return "draw" if all(state) else None

    def evaluate(self, state: tuple[str, ...], root_player: str, outcome: str | None, remaining_depth: int) -> float:
        if outcome == root_player:
            return 100.0 + remaining_depth
        if outcome in {"X", "O"}:
            return -100.0 - remaining_depth
        if outcome == "draw":
            return 0.0
        opponent = "O" if root_player == "X" else "X"
        score = 0
        for line in self.wins:
            values = [state[index] for index in line]
            if opponent not in values:
                score += values.count(root_player) * 2
            if root_player not in values:
                score -= values.count(opponent) * 2
        return float(score)

    def key(self, state: tuple[str, ...]) -> str:
        return "".join(cell or "." for cell in state)


class TicTacToeEngine(GameSearchEngine[tuple[str, ...], int]):
    algorithm_id = "tic-tac-toe"

    def __init__(self, config: TicTacToeConfig) -> None:
        self.config = config
        super().__init__(config, TicTacToeGame(), tuple(config.board), "O" if config.player == "X" else "X")


def available_moves(board: list[str] | tuple[str, ...]) -> list[int]:
    """Return legal cell indexes in deterministic order."""
    return TicTacToeGame().legal_moves(tuple("" if cell == "." else cell for cell in board))
