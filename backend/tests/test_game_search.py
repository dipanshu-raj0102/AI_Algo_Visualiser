from app.algorithms.connect_four import ConnectFourConfig, ConnectFourEngine
from app.algorithms.game_search import MinimaxAlphaBetaEngine, MinimaxConfig, generate_search_tree
from app.algorithms.tic_tac_toe import TicTacToeConfig, TicTacToeEngine


def test_tic_tac_toe_takes_immediate_win_and_emits_search_events():
    result = TicTacToeEngine(
        TicTacToeConfig(board=["X", "X", "", "O", "O", "", "", "", ""], player="X")
    ).run()

    assert result.status == "completed"
    assert result.final_state.metadata["selected_move"] == 2
    assert isinstance(result.final_state.metrics["nodes_visited"], (int, float))
    assert result.final_state.metrics["nodes_visited"] > 1
    assert {event.event_type for event in result.events} >= {
        "TRAVERSAL",
        "ALPHA_BETA",
        "MOVE_SELECTED",
        "COMPLETED",
    }


def test_terminal_game_outcomes_are_reported_without_expanding():
    tic_tac_toe = TicTacToeEngine(
        TicTacToeConfig(board=["X", "X", "X", "O", "O", "", "", "", ""], player="O")
    ).run()
    assert tic_tac_toe.final_state.metadata["outcome"] == "X"
    assert tic_tac_toe.final_state.metrics["nodes_visited"] == 1

    board = [""] * (6 * 7)
    board[35:39] = ["X", "X", "X", "X"]
    connect_four = ConnectFourEngine(ConnectFourConfig(board=board, player="O", max_depth=2)).run()
    assert connect_four.final_state.metadata["outcome"] == "X"
    assert connect_four.final_state.metrics["nodes_visited"] == 1


def test_generic_alpha_beta_reports_real_pruning():
    config = MinimaxConfig(depth=5, branching_factor=3, seed=11)
    result = MinimaxAlphaBetaEngine(config).run()

    assert result.status == "completed"
    assert isinstance(result.final_state.metrics["cutoffs"], (int, float))
    assert isinstance(result.final_state.metrics["pruned_branches"], (int, float))
    assert result.final_state.metrics["cutoffs"] > 0
    assert result.final_state.metrics["pruned_branches"] > 0
    assert any(event.event_type == "PRUNED_BRANCH" for event in result.events)


def test_seeded_tree_generation_and_trace_are_reproducible():
    config = MinimaxConfig(depth=3, branching_factor=2, seed=91)
    first_tree = generate_search_tree(config)
    second_tree = generate_search_tree(config)
    assert first_tree == second_tree

    first = MinimaxAlphaBetaEngine(config, first_tree).run()
    second = MinimaxAlphaBetaEngine(config, second_tree).run()
    assert [event.model_dump() for event in first.events] == [event.model_dump() for event in second.events]


def test_connect_four_is_bounded_and_selects_a_legal_column():
    config = ConnectFourConfig(max_depth=2)
    result = ConnectFourEngine(config).run()

    assert result.status == "completed"
    assert isinstance(result.final_state.metrics["max_depth"], (int, float))
    assert result.final_state.metrics["max_depth"] <= 2
    assert result.final_state.metadata["selected_move"] in range(config.cols)
