from typing import cast

from app.algorithms.function_landscape import (
    FunctionLandscapeConfig,
    FunctionLandscapeEngine,
    FunctionLandscapeSimulatedAnnealingEngine,
)
from app.algorithms.local_search import HillClimbingConfig, HillClimbingEngine, SimulatedAnnealingConfig, SimulatedAnnealingEngine
from app.algorithms.n_queens import NQueensConfig, NQueensSimulatedAnnealingEngine, queen_conflicts
from app.algorithms.tsp import TSPConfig, TSPSimulatedAnnealingEngine, tour_distance


class IntegerClimber(HillClimbingEngine[int]):
    def initial_state(self, rng, restart=0):
        return 0 if restart == 0 else rng.randint(-2, 2)

    def objective(self, state):
        return -(state - 3) ** 2

    def neighbours(self, state, rng):
        return [state - 1, state + 1]


def test_reusable_hill_climbing_terminates_and_emits_move_sequence():
    result = IntegerClimber(HillClimbingConfig(max_iterations=20, restarts=1, seed=19)).run()

    assert result.status == "completed"
    assert result.final_state.event_type == "COMPLETED"
    assert result.final_state.metadata["best_solution"] == 3
    event_types = [event.event_type for event in result.events]
    assert event_types[0:2] == ["INITIALIZED", "BEST_SOLUTION"]
    assert "CANDIDATE_EVALUATED" in event_types
    assert "MOVE_ACCEPTED" in event_types
    assert "MOVE_REJECTED" in event_types
    assert event_types[-1] == "COMPLETED"
    assert [event.model_dump() for event in result.events] == [
        event.model_dump() for event in IntegerClimber(HillClimbingConfig(max_iterations=20, restarts=1, seed=19)).run().events
    ]


def test_simulated_annealing_reports_temperature_and_is_seeded():
    class OneDimensionalAnnealer(SimulatedAnnealingEngine[int]):
        def initial_state(self, rng, restart=0):
            return 0

        def objective(self, state):
            return -(state - 4) ** 2

        def neighbours(self, state, rng):
            return [state - 1, state + 1]

    config = SimulatedAnnealingConfig(max_iterations=12, seed=7, initial_temperature=3, cooling_rate=0.8)
    first = OneDimensionalAnnealer(config).run()
    second = OneDimensionalAnnealer(config).run()
    assert [event.model_dump() for event in first.events] == [event.model_dump() for event in second.events]
    assert any(event.event_type == "TEMPERATURE_UPDATED" for event in first.events)
    assert all("temperature" in event.metrics for event in first.events)
    assert first.final_state.metrics["candidate_evaluations"] == 12


def test_function_landscape_reaches_a_local_peak_reproducibly():
    config = FunctionLandscapeConfig(function_name="quadratic", target=1.0, initial_x=-2.0, step_size=0.5, max_iterations=20)
    first = FunctionLandscapeEngine(config).run()
    second = FunctionLandscapeEngine(config).run()
    assert [event.model_dump() for event in first.events] == [event.model_dump() for event in second.events]
    best_x = cast(float, first.final_state.metadata["best_solution"])
    best_score = cast(float, first.final_state.metadata["best_score"])
    assert abs(best_x - 1.0) < 0.51
    assert best_score <= 0


def test_n_queens_and_tsp_report_valid_best_solutions():
    queens = NQueensSimulatedAnnealingEngine(
        NQueensConfig(n=4, initial_board=[1, 3, 0, 2], max_iterations=10, seed=3)
    ).run()
    queen_board = cast(list[int], queens.final_state.metadata["best_solution"])
    assert queen_conflicts(queen_board) == 0
    assert any(event.event_type == "BEST_SOLUTION" for event in queens.events)

    cities = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    tsp = TSPSimulatedAnnealingEngine(
        TSPConfig(cities=cities, initial_tour=[0, 1, 2, 3], max_iterations=8, seed=3)
    ).run()
    tour = cast(list[int], tsp.final_state.metadata["best_solution"])
    assert sorted(tour) == list(range(4))
    assert tour_distance(tour, cities) >= 4
    best_score = cast(float, tsp.final_state.metadata["best_score"])
    assert best_score == -tour_distance(tour, cities)
