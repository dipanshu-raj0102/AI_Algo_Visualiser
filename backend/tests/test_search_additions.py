from app.algorithms.greedy_best_first_grid import GreedyBestFirstGridConfig, GreedyBestFirstGridEngine
from app.algorithms.heuristic_comparison import (
    HeuristicComparisonConfig,
    HeuristicComparisonEngine,
    compare_heuristics,
)
from app.algorithms.weighted_astar_grid import WeightedAStarGridConfig, WeightedAStarGridEngine, generate_terrain


def _without_timing(value):
    if isinstance(value, dict):
        return {key: _without_timing(item) for key, item in value.items() if key != "execution_time"}
    if isinstance(value, list):
        return [_without_timing(item) for item in value]
    return value


def test_greedy_best_first_reaches_goal_with_deterministic_events():
    config = GreedyBestFirstGridConfig(rows=5, cols=5, start="0,0", goal="4,4", obstacles=["1,1"])
    first = GreedyBestFirstGridEngine(config).run()
    second = GreedyBestFirstGridEngine(config).run()

    assert first.status == "completed"
    assert first.final_state.path[0] == "0,0"
    assert first.final_state.path[-1] == "4,4"
    assert [event.model_dump() for event in first.events] == [event.model_dump() for event in second.events]
    assert first.events[0].metadata["strategy"] == "greedy-best-first"
    assert first.events[-1].event_type == "COMPLETED"


def test_weighted_astar_prefers_lower_cost_detour():
    config = WeightedAStarGridConfig(
        rows=4,
        cols=5,
        start="0,0",
        goal="0,4",
        terrain_max=10,
        terrain={"0,1": 10, "0,2": 10, "0,3": 10, "0,4": 10},
    )
    result = WeightedAStarGridEngine(config).run()

    assert result.status == "completed"
    assert result.final_state.metrics["path_cost"] == 15
    assert not {"0,1", "0,2", "0,3"}.issubset(set(result.final_state.path))
    assert result.final_state.path[0] == "0,0"
    assert result.final_state.path[-1] == "0,4"
    assert result.events[0].metadata["terrain"]["0,1"] == 10.0
    assert result.events[-1].event_type == "COMPLETED"


def test_weighted_terrain_generation_is_seeded_and_replayable():
    config = WeightedAStarGridConfig(rows=6, cols=6, start="0,0", goal="5,5", terrain_min=1, terrain_max=4, seed=21)
    terrain = generate_terrain(config)
    assert terrain == generate_terrain(config)

    first = WeightedAStarGridEngine(config.model_copy(update={"terrain": terrain})).run()
    second = WeightedAStarGridEngine(config.model_copy(update={"terrain": terrain})).run()
    assert first.status == "completed"
    assert [event.model_dump() for event in first.events] == [event.model_dump() for event in second.events]


def test_heuristic_comparison_reuses_astar_and_reports_each_run():
    config = HeuristicComparisonConfig(
        grid={"rows": 5, "cols": 5, "start": "0,0", "goal": "4,4", "obstacle_density": 0},
        heuristics=["manhattan", "euclidean"],
    )
    first = HeuristicComparisonEngine(config).run()
    second = HeuristicComparisonEngine(config).run()
    summaries = compare_heuristics(config)

    assert first.status == "completed"
    assert [event.event_type for event in first.events] == ["INITIALIZED", "HEURISTIC_COMPLETED", "HEURISTIC_COMPLETED", "COMPLETED"]
    assert first.final_state.metrics["completed_runs"] == 2
    assert first.final_state.metadata["best_heuristic"] in {"manhattan", "euclidean"}
    assert [summary.path_cost for summary in summaries] == [8.0, 8.0]
    # Search decisions and replay payloads are deterministic; wall-clock timing
    # is intentionally measured per execution and may vary between runs.
    assert [_without_timing(event.model_dump()) for event in first.events] == [_without_timing(event.model_dump()) for event in second.events]
