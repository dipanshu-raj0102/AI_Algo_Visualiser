from fastapi.testclient import TestClient
from typing import cast

from app.algorithms.graph_variants import CityMapAStarEngine, CityMapConfig, WebCrawlerBestFirstEngine, WebCrawlerConfig
from app.algorithms.puzzle import FifteenPuzzleEngine, PuzzleConfig, puzzle_solvable
from app.algorithms.heuristic_comparison import HeuristicComparisonConfig, HeuristicComparisonEngine
from app.algorithms.astar_grid import AStarGridConfig
from app.algorithms.move_ordering import MoveOrderingConfig, MoveOrderingImpactEngine
from app.main import app


client = TestClient(app)


def test_registry_exposes_real_algorithm_families():
    ids = {item["id"] for item in client.get("/api/v1/algorithms").json()}
    assert {"greedy-best-first-grid", "weighted-astar-grid", "tic-tac-toe", "simulated-annealing-scheduling"}.issubset(ids)


def test_comparison_reuses_the_same_grid_problem():
    response = client.post("/api/v1/comparisons", json={"algorithm_ids": ["astar-grid", "greedy-best-first-grid"], "config": {"rows": 5, "cols": 5, "start": "0,0", "goal": "4,4", "obstacle_density": 0, "seed": 3}})
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    first_grid = results[0]["events"][0]["metadata"]["grid"]
    second_grid = results[1]["events"][0]["metadata"]["grid"]
    assert first_grid == second_grid


def test_fifteen_puzzle_goal_is_solvable_and_one_move_completes():
    goal = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0]
    assert puzzle_solvable(goal)
    result = FifteenPuzzleEngine(PuzzleConfig(board=goal[:-2] + [0, 15])).run()
    assert result.status == "completed"
    assert result.final_state.metrics["path_cost"] == 1


def test_city_map_and_crawler_emit_completed_event():
    city = CityMapAStarEngine(CityMapConfig()).run()
    crawler = WebCrawlerBestFirstEngine(WebCrawlerConfig()).run()
    assert city.status == "completed"
    assert crawler.status == "completed"
    assert city.events[-1].event_type == "COMPLETED"
    assert crawler.events[-1].metadata["visit_order"]


def test_heuristic_analysis_supports_dijkstra_and_chebyshev():
    result = HeuristicComparisonEngine(HeuristicComparisonConfig(grid=AStarGridConfig(rows=5, cols=5, start="0,0", goal="4,4", obstacle_density=0), heuristics=["manhattan", "euclidean", "chebyshev", "zero"])).run()
    assert result.status == "completed"
    assert result.final_state.metadata["best_heuristic"] in {"manhattan", "euclidean", "chebyshev", "zero"}


def test_move_ordering_compares_two_traversals_on_one_tree():
    result = MoveOrderingImpactEngine(MoveOrderingConfig(depth=3, branching_factor=3, seed=9)).run()
    assert result.status == "completed"
    runs = cast(list[dict[str, object]], result.final_state.metadata["runs"])
    assert [run["label"] for run in runs] == ["good-ordering", "bad-ordering"]
