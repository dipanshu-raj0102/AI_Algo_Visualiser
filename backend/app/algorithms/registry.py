from dataclasses import dataclass
from typing import Any, Callable

from .astar_grid import AStarGridConfig, AStarGridEngine


@dataclass(frozen=True)
class AlgorithmDefinition:
    id: str
    name: str
    category: str
    description: str
    difficulty: str
    visualization_type: str
    supports_step_execution: bool
    supports_comparison: bool
    config_model: type
    engine_factory: Callable[[Any], Any]


REGISTRY = {
    "astar-grid": AlgorithmDefinition(
        id="astar-grid",
        name="A* Grid Pathfinding",
        category="Informed Search",
        description="Watch A* balance path cost g(n) and estimated distance h(n) to find an optimal route through obstacles.",
        difficulty="Intermediate",
        visualization_type="grid",
        supports_step_execution=True,
        supports_comparison=True,
        config_model=AStarGridConfig,
        engine_factory=AStarGridEngine,
    )
}


def list_metadata() -> list[dict[str, object]]:
    return [
        {key: value for key, value in definition.__dict__.items() if key not in {"config_model", "engine_factory"}}
        for definition in REGISTRY.values()
    ]
