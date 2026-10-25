from app.algorithms.astar_grid import AStarGridConfig, AStarGridEngine, generate_obstacles


def run(config: AStarGridConfig):
    return AStarGridEngine(config).run()


def test_astar_finds_optimal_open_grid_route():
    result = run(AStarGridConfig(rows=4, cols=4, start="0,0", goal="3,3", obstacles=[]))
    assert result.status == "completed"
    assert result.final_state.path[0] == "0,0"
    assert result.final_state.path[-1] == "3,3"
    assert result.final_state.metrics["path_cost"] == 6


def test_astar_routes_around_obstacles():
    obstacles = ["1,0", "1,1", "1,2"]
    result = run(AStarGridConfig(rows=4, cols=4, start="0,0", goal="3,3", obstacles=obstacles))
    assert result.status == "completed"
    assert not set(result.final_state.path).intersection(obstacles)
    assert result.final_state.metrics["path_cost"] == 6


def test_seeded_generation_is_reproducible_and_preserves_corridor():
    config = AStarGridConfig(rows=8, cols=8, start="0,0", goal="7,7", obstacle_density=0.35, seed=17)
    assert generate_obstacles(config) == generate_obstacles(config)
    result = run(config.model_copy(update={"obstacles": generate_obstacles(config)}))
    assert result.status == "completed"


def test_invalid_heuristic_is_rejected():
    try:
        AStarGridConfig(heuristic="not-a-heuristic")
    except ValueError as exc:
        assert "heuristic" in str(exc)
    else:
        raise AssertionError("Expected invalid heuristic to be rejected")
