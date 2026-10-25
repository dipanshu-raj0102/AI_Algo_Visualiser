import pytest

from app.algorithms.astar_grid import AStarGridConfig
from app.algorithms.heuristic_comparison import HeuristicComparisonConfig, HeuristicComparisonEngine


def _without_timing(value):
    if isinstance(value, dict):
        return {key: _without_timing(item) for key, item in value.items() if key != "execution_time"}
    if isinstance(value, list):
        return [_without_timing(item) for item in value]
    return value


def test_comparison_materializes_one_exact_problem_for_all_heuristics():
    result = HeuristicComparisonEngine(
        HeuristicComparisonConfig(
            grid=AStarGridConfig(rows=7, cols=7, start="0,0", goal="6,6", obstacle_density=0.25, seed=19),
        )
    ).run()

    runs = result.final_state.metadata["runs"]
    assert len(runs) == 4
    problems = [run["problem"] for run in runs]
    assert all(problem == problems[0] for problem in problems)
    assert {run["heuristic"] for run in runs} == {"manhattan", "euclidean", "chebyshev", "zero"}
    assert all(run["events"][0]["metadata"]["seed"] == 19 for run in runs)


def test_comparison_trace_is_deterministic_except_wall_clock_metric():
    config = HeuristicComparisonConfig(grid=AStarGridConfig(rows=6, cols=6, start="0,0", goal="5,5", seed=7))
    first = HeuristicComparisonEngine(config).run()
    second = HeuristicComparisonEngine(config).run()

    assert _without_timing(first.model_dump()) == _without_timing(second.model_dump())
    assert all(run["execution_time"] >= 0 for run in first.final_state.metadata["runs"])


def test_zero_heuristic_is_dijkstra_and_exposes_formula():
    result = HeuristicComparisonEngine(
        HeuristicComparisonConfig(
            grid=AStarGridConfig(rows=5, cols=5, start="0,0", goal="4,4", obstacle_density=0),
            heuristics=["zero"],
        )
    ).run()
    run = result.final_state.metadata["runs"][0]

    assert run["heuristic"] == "zero"
    assert run["events"][0]["metadata"]["heuristic_formula"] == "0"
    assert "Dijkstra" in run["events"][0]["metadata"]["heuristic_description"]
    assert all(item["h"] == 0 for event in run["events"] for item in event["frontier"])


def test_comparison_reports_real_reachability_metrics_and_replay_steps():
    result = HeuristicComparisonEngine(
        HeuristicComparisonConfig(grid=AStarGridConfig(rows=5, cols=5, start="0,0", goal="4,4", obstacle_density=0))
    ).run()
    run = result.final_state.metadata["runs"][0]

    assert {"expanded", "discovered", "max_frontier", "path_length", "path_cost", "explored_cells", "execution_time", "reached", "steps"}.issubset(run)
    assert run["reached"] is True
    assert run["path_cost"] == 8
    assert run["path_length"] == 9
    assert run["expanded"] == run["explored_cells"]
    assert run["steps"] > 0
    assert run["events"][-1]["event_type"] == "COMPLETED"


def test_no_path_is_reported_for_each_heuristic_and_invalid_points_are_rejected():
    config = HeuristicComparisonConfig(
        grid=AStarGridConfig(rows=4, cols=4, start="0,0", goal="3,3", obstacles=["0,1", "1,0", "1,1"])
    )
    result = HeuristicComparisonEngine(config).run()
    assert all(run["reached"] is False and run["path_cost"] is None for run in result.final_state.metadata["runs"])

    same_point = HeuristicComparisonEngine(HeuristicComparisonConfig(grid=AStarGridConfig(rows=4, cols=4, start="1,1", goal="1,1"))).run()
    assert all(run["reached"] is True and run["path_cost"] == 0 for run in same_point.final_state.metadata["runs"])
    with pytest.raises(ValueError, match="cannot be obstacles"):
        AStarGridConfig(rows=4, cols=4, start="0,0", goal="3,3", obstacles=["0, 0"])
