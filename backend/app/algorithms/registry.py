from dataclasses import dataclass
from typing import Any, Callable

from .astar_grid import AStarGridConfig, AStarGridEngine
from .connect_four import ConnectFourConfig, ConnectFourEngine
from .function_landscape import FunctionLandscapeConfig, FunctionLandscapeHillClimbingEngine, FunctionLandscapeSimulatedAnnealingEngine
from .graph_variants import CityMapAStarEngine, CityMapConfig, LandmarkRouteConfig, LandmarkRouteEngine, WebCrawlerBestFirstEngine, WebCrawlerConfig
from .game_search import MinimaxAlphaBetaEngine, MinimaxConfig
from .move_ordering import MoveOrderingConfig, MoveOrderingImpactEngine
from .greedy_best_first_grid import GreedyBestFirstGridConfig, GreedyBestFirstGridEngine
from .heuristic_comparison import HeuristicComparisonConfig, HeuristicComparisonEngine
from .n_queens import NQueensConfig, NQueensHillClimbingEngine, NQueensSimulatedAnnealingEngine
from .tic_tac_toe import TicTacToeConfig, TicTacToeEngine
from .tsp import TSPConfig, TSPHillClimbingEngine, TSPSimulatedAnnealingEngine
from .weighted_astar_grid import WeightedAStarGridConfig, WeightedAStarGridEngine
from .puzzle import FifteenPuzzleEngine, PuzzleConfig
from .scheduling import SchedulingAnnealingEngine, SchedulingConfig


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


def definition(id: str, name: str, category: str, description: str, difficulty: str, visualization_type: str, config_model: type, engine_factory: Callable[[Any], Any], supports_comparison: bool = True) -> AlgorithmDefinition:
    return AlgorithmDefinition(id, name, category, description, difficulty, visualization_type, True, supports_comparison, config_model, engine_factory)


REGISTRY: dict[str, AlgorithmDefinition] = {
    "astar-grid": definition("astar-grid", "A* Grid Pathfinding", "Informed Search", "Find an optimal route by balancing path cost and a heuristic estimate.", "Intermediate", "grid", AStarGridConfig, AStarGridEngine),
    "greedy-best-first-grid": definition("greedy-best-first-grid", "Greedy Best-First Search", "Best-First Search", "Explore the node that appears closest to the goal according to h(n).", "Intermediate", "grid", GreedyBestFirstGridConfig, GreedyBestFirstGridEngine),
    "weighted-astar-grid": definition("weighted-astar-grid", "Weighted Terrain A*", "Informed Search", "Find a least-cost route through configurable terrain costs.", "Intermediate", "terrain-grid", WeightedAStarGridConfig, WeightedAStarGridEngine),
    "astar-heuristic-comparison": definition("astar-heuristic-comparison", "Heuristic Impact Analysis", "Informed Search", "Compare A* heuristics on the exact same seeded problem.", "Advanced", "comparison-grid", HeuristicComparisonConfig, HeuristicComparisonEngine),
    "function-landscape-hill-climbing": definition("function-landscape-hill-climbing", "Hill Climbing on a Landscape", "Local Search", "Climb a mathematical landscape and observe local optima.", "Intermediate", "landscape", FunctionLandscapeConfig, FunctionLandscapeHillClimbingEngine),
    "function-landscape-simulated-annealing": definition("function-landscape-simulated-annealing", "Annealing on a Landscape", "Optimization", "Explore a rugged landscape while cooling the search temperature.", "Intermediate", "landscape", FunctionLandscapeConfig, FunctionLandscapeSimulatedAnnealingEngine),
    "n-queens-hill-climbing": definition("n-queens-hill-climbing", "N-Queens Hill Climbing", "Local Search", "Minimize attacking queen pairs with local improvement.", "Intermediate", "board", NQueensConfig, NQueensHillClimbingEngine),
    "n-queens-simulated-annealing": definition("n-queens-simulated-annealing", "N-Queens Simulated Annealing", "Optimization", "Use temperature-driven exploration to escape queen conflicts.", "Intermediate", "board", NQueensConfig, NQueensSimulatedAnnealingEngine),
    "tsp-hill-climbing": definition("tsp-hill-climbing", "TSP Hill Climbing", "Local Search", "Improve a city tour with neighborhood swaps.", "Intermediate", "route", TSPConfig, TSPHillClimbingEngine),
    "tsp-simulated-annealing": definition("tsp-simulated-annealing", "TSP Simulated Annealing", "Optimization", "Explore alternative tours while cooling toward a good route.", "Advanced", "route", TSPConfig, TSPSimulatedAnnealingEngine),
    "minimax-alpha-beta": definition("minimax-alpha-beta", "Generic Minimax / Alpha-Beta", "Game Search", "Traverse a deterministic game tree and inspect real pruning decisions.", "Advanced", "tree", MinimaxConfig, MinimaxAlphaBetaEngine),
    "tic-tac-toe": definition("tic-tac-toe", "Tic-Tac-Toe Alpha-Beta", "Game Search", "Play or inspect a complete Tic-Tac-Toe search tree.", "Intermediate", "board-tree", TicTacToeConfig, TicTacToeEngine, False),
    "connect-four": definition("connect-four", "Connect-4 Alpha-Beta", "Game Search", "Explore a bounded Connect-4 decision with depth-limited search.", "Advanced", "board-tree", ConnectFourConfig, ConnectFourEngine, False),
    "astar-city-map": definition("astar-city-map", "A* Weighted City Map", "Informed Search", "Find an optimal route across a weighted city graph.", "Intermediate", "graph", CityMapConfig, CityMapAStarEngine),
    "astar-15-puzzle": definition("astar-15-puzzle", "A* 15-Puzzle", "Informed Search", "Solve a 15-puzzle with Manhattan distance and replay the move sequence.", "Advanced", "puzzle", PuzzleConfig, FifteenPuzzleEngine),
    "web-crawler-best-first": definition("web-crawler-best-first", "Best-First Web Crawler", "Best-First Search", "Prioritize conceptual pages by relevance without crawling the real web.", "Beginner", "graph", WebCrawlerConfig, WebCrawlerBestFirstEngine),
    "landmark-best-first": definition("landmark-best-first", "Landmark Route Finding", "Best-First Search", "Use straight-line landmark distance to guide a greedy route search.", "Intermediate", "graph", LandmarkRouteConfig, LandmarkRouteEngine),
    "simulated-annealing-scheduling": definition("simulated-annealing-scheduling", "Annealing Timetable Scheduling", "Optimization", "Reduce timetable conflicts and makespan through temperature-driven search.", "Advanced", "schedule", SchedulingConfig, SchedulingAnnealingEngine),
    "alpha-beta-move-ordering": definition("alpha-beta-move-ordering", "Move Ordering Impact", "Game Search", "Compare alpha-beta pruning with good and bad traversal order on one tree.", "Advanced", "comparison-tree", MoveOrderingConfig, MoveOrderingImpactEngine),
}


def list_metadata() -> list[dict[str, object]]:
    return [
        {key: value for key, value in algorithm.__dict__.items() if key not in {"config_model", "engine_factory"}}
        for algorithm in REGISTRY.values()
    ]
