"""Limited-depth Connect-4 minimax/alpha-beta visualisation engine."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from .game_search import GameAdapter, GameSearchEngine


class ConnectFourConfig(BaseModel):
    rows: int = Field(default=6, ge=4, le=8)
    cols: int = Field(default=7, ge=4, le=10)
    board: list[str] | None = None
    player: str = "X"
    max_depth: int = Field(default=4, ge=0, le=8)
    alpha_beta: bool = True

    @field_validator("player")
    @classmethod
    def validate_player(cls, value: str) -> str:
        if value not in {"X", "O"}:
            raise ValueError("player must be X or O")
        return value

    @model_validator(mode="after")
    def validate_board(self) -> "ConnectFourConfig":
        expected = self.rows * self.cols
        if self.board is None:
            self.board = [""] * expected
        if len(self.board) != expected:
            raise ValueError(f"Connect-4 board must contain {expected} cells")
        if any(cell not in {"", ".", "X", "O"} for cell in self.board):
            raise ValueError("board cells must be empty, X, or O")
        self.board = ["" if cell == "." else cell for cell in self.board]
        return self


class ConnectFourGame(GameAdapter[tuple[str, ...], int]):
    def __init__(self, rows: int, cols: int) -> None:
        self.rows, self.cols = rows, cols

    def legal_moves(self, state: tuple[str, ...]) -> list[int]:
        return [col for col in range(self.cols) if not state[col]]

    def apply_move(self, state: tuple[str, ...], move: int, player: str) -> tuple[str, ...]:
        board = list(state)
        for row in range(self.rows - 1, -1, -1):
            index = row * self.cols + move
            if not board[index]:
                board[index] = player
                return tuple(board)
        raise ValueError("cannot play in a full Connect-4 column")

    def _lines(self, state: tuple[str, ...]) -> list[list[str]]:
        lines: list[list[str]] = []
        for row in range(self.rows):
            for col in range(self.cols - 3):
                lines.append([state[row * self.cols + col + offset] for offset in range(4)])
        for row in range(self.rows - 3):
            for col in range(self.cols):
                lines.append([state[(row + offset) * self.cols + col] for offset in range(4)])
        for row in range(self.rows - 3):
            for col in range(self.cols - 3):
                lines.append([state[(row + offset) * self.cols + col + offset] for offset in range(4)])
        for row in range(3, self.rows):
            for col in range(self.cols - 3):
                lines.append([state[(row - offset) * self.cols + col + offset] for offset in range(4)])
        return lines

    def terminal(self, state: tuple[str, ...]) -> str | None:
        for line in self._lines(state):
            if line[0] and line.count(line[0]) == 4:
                return line[0]
        return "draw" if all(state) else None

    def evaluate(self, state: tuple[str, ...], root_player: str, outcome: str | None, remaining_depth: int) -> float:
        if outcome == root_player:
            return 100_000.0 + remaining_depth
        if outcome in {"X", "O"}:
            return -100_000.0 - remaining_depth
        if outcome == "draw":
            return 0.0
        opponent = "O" if root_player == "X" else "X"
        score = 0.0
        for line in self._lines(state):
            if opponent not in line:
                score += (1, 10, 100, 1000)[line.count(root_player)]
            if root_player not in line:
                score -= (1, 10, 100, 1000)[line.count(opponent)]
        return score

    def key(self, state: tuple[str, ...]) -> str:
        return "/".join("".join(cell or "." for cell in state[row * self.cols : (row + 1) * self.cols]) for row in range(self.rows))


class ConnectFourEngine(GameSearchEngine[tuple[str, ...], int]):
    algorithm_id = "connect-four"

    def __init__(self, config: ConnectFourConfig) -> None:
        super().__init__(config, ConnectFourGame(config.rows, config.cols), tuple(config.board or []), "O" if config.player == "X" else "X")


Connect4Config = ConnectFourConfig
Connect4Engine = ConnectFourEngine
