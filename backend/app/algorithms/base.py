from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


ConfigT = TypeVar("ConfigT", bound=BaseModel)


class AlgorithmEvent(BaseModel):
    """A serializable state transition consumed by visualizers."""

    model_config = ConfigDict(extra="forbid")

    iteration: int = Field(ge=0)
    event_type: str
    current_node: str | None = None
    frontier: list[dict] = Field(default_factory=list)
    explored: list[str] = Field(default_factory=list)
    path: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | None] = Field(default_factory=dict)
    metadata: dict[str, object] = Field(default_factory=dict)


class AlgorithmResult(BaseModel):
    algorithm_id: str
    status: str
    events: list[AlgorithmEvent]
    final_state: AlgorithmEvent


class AlgorithmEngine(ABC, Generic[ConfigT]):
    """Common contract for deterministic, replayable algorithm engines."""

    algorithm_id: str

    def __init__(self, config: ConfigT) -> None:
        self.config = config
        self.events: list[AlgorithmEvent] = []

    @abstractmethod
    def run(self) -> AlgorithmResult:
        """Execute the algorithm and return its event log."""

    def record(self, event: AlgorithmEvent) -> None:
        self.events.append(event)
