"""Deterministic minimax and alpha-beta search engines.

The module contains two layers: a small generic tree search useful for
visualising alpha-beta itself, and a game adapter used by the Tic-Tac-Toe and
Connect-4 engines.  Both layers use the project's event contract so their
executions can be replayed by the visualiser.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


@dataclass(frozen=True)
class SearchTreeNode:
    """A deterministic, immutable game-tree node."""

    node_id: str
    children: tuple["SearchTreeNode", ...] = ()
    value: float | None = None

    @property
    def is_leaf(self) -> bool:
        return not self.children


class TreeGenerationConfig(BaseModel):
    """Controls reproducible synthetic trees used by the generic engine."""

    depth: int = Field(default=4, ge=0, le=12)
    branching_factor: int = Field(default=3, ge=1, le=8)
    seed: int = Field(default=482193, ge=0, le=2_147_483_647)
    leaf_min: int = -100
    leaf_max: int = 100
    leaf_values: list[int] | None = None

    @model_validator(mode="after")
    def validate_leaf_range(self) -> "TreeGenerationConfig":
        if self.leaf_min > self.leaf_max:
            raise ValueError("leaf_min must not exceed leaf_max")
        return self


def generate_search_tree(config: TreeGenerationConfig | None = None, **kwargs: Any) -> SearchTreeNode:
    """Generate the same tree for the same configuration, including seed."""

    if config is None:
        config = TreeGenerationConfig(**kwargs)
    elif kwargs:
        raise TypeError("pass either a tree configuration or generation keyword arguments, not both")

    rng = random.Random(config.seed)

    def build(node_id: str, depth: int) -> SearchTreeNode:
        if depth >= config.depth:
            value = rng.choice(config.leaf_values) if config.leaf_values else rng.randint(config.leaf_min, config.leaf_max)
            return SearchTreeNode(node_id=node_id, value=value)
        children = tuple(build(f"{node_id}.{index}", depth + 1) for index in range(config.branching_factor))
        return SearchTreeNode(node_id=node_id, children=children)

    return build("root", 0)


class MinimaxConfig(TreeGenerationConfig):
    """Configuration for :class:`MinimaxAlphaBetaEngine`."""

    alpha_beta: bool = True


class MinimaxAlphaBetaEngine(AlgorithmEngine[MinimaxConfig]):
    """Run minimax over a generated or caller-supplied deterministic tree."""

    algorithm_id = "minimax-alpha-beta"

    def __init__(self, config: MinimaxConfig, root: SearchTreeNode | None = None) -> None:
        super().__init__(config)
        self.root = root or generate_search_tree(config)
        self.nodes_visited = 0
        self.leaves_evaluated = 0
        self.cutoffs = 0
        self.pruned_branches = 0
        self.max_depth_reached = 0
        self.root_child_values: dict[str, float] = {}

    def _bounds(self, value: float) -> float | int | None:
        return None if math.isinf(value) else value

    def _record_search(
        self,
        event_type: str,
        node: SearchTreeNode,
        depth: int,
        *,
        node_type: str,
        alpha: float,
        beta: float,
        value: float | None = None,
        **metadata: Any,
    ) -> None:
        metrics: dict[str, int | float | str | None] = {
            "nodes_visited": self.nodes_visited,
            "leaves_evaluated": self.leaves_evaluated,
            "cutoffs": self.cutoffs,
            "pruned_branches": self.pruned_branches,
            "depth": depth,
            "alpha": self._bounds(alpha),
            "beta": self._bounds(beta),
        }
        if value is not None:
            metrics["value"] = value
        self.record(
            AlgorithmEvent(
                iteration=len(self.events),
                event_type=event_type,
                current_node=node.node_id,
                metrics=metrics,
                metadata={
                    "node_type": node_type,
                    "alpha": self._bounds(alpha),
                    "beta": self._bounds(beta),
                    **metadata,
                },
            )
        )

    def _search(self, node: SearchTreeNode, depth: int, maximizing: bool, alpha: float, beta: float) -> float:
        self.nodes_visited += 1
        self.max_depth_reached = max(self.max_depth_reached, depth)
        self._record_search(
            "TRAVERSAL", node, depth, node_type="MAX" if maximizing else "MIN", alpha=alpha, beta=beta
        )
        if node.is_leaf:
            self.leaves_evaluated += 1
            value = float(node.value or 0)
            self._record_search("NODE_EVALUATED", node, depth, node_type="LEAF", alpha=alpha, beta=beta, value=value)
            return value

        best = -math.inf if maximizing else math.inf
        for index, child in enumerate(node.children):
            value = self._search(child, depth + 1, not maximizing, alpha, beta)
            if depth == 0:
                self.root_child_values[child.node_id] = value
            if maximizing:
                best = max(best, value)
                alpha = max(alpha, best)
            else:
                best = min(best, value)
                beta = min(beta, best)
            self._record_search(
                "ALPHA_BETA",
                node,
                depth,
                node_type="MAX" if maximizing else "MIN",
                alpha=alpha,
                beta=beta,
                value=best,
                child=child.node_id,
            )
            if self.config.alpha_beta and alpha >= beta:
                remaining = len(node.children) - index - 1
                if remaining:
                    self.cutoffs += 1
                    self.pruned_branches += remaining
                    self._record_search(
                        "CUTOFF",
                        node,
                        depth,
                        node_type="MAX" if maximizing else "MIN",
                        alpha=alpha,
                        beta=beta,
                        cutoff_child=child.node_id,
                        pruned_count=remaining,
                    )
                    for pruned in node.children[index + 1 :]:
                        self._record_search(
                            "PRUNED_BRANCH",
                            pruned,
                            depth + 1,
                            node_type="PRUNED",
                            alpha=alpha,
                            beta=beta,
                            parent=node.node_id,
                        )
                break
        return best

    def run(self) -> AlgorithmResult:
        self.events = []
        self.nodes_visited = self.leaves_evaluated = self.cutoffs = self.pruned_branches = 0
        self.max_depth_reached = 0
        self.root_child_values = {}
        self.record(
            AlgorithmEvent(
                iteration=0,
                event_type="INITIALIZED",
                current_node=self.root.node_id,
                metadata={"strategy": "minimax", "alpha_beta": self.config.alpha_beta, "seed": self.config.seed},
            )
        )
        value = self._search(self.root, 0, True, -math.inf, math.inf)
        selected_move = None
        if self.root_child_values:
            selected_move = max(self.root_child_values, key=lambda child_id: self.root_child_values[child_id])
        metrics = {
            "value": value,
            "nodes_visited": self.nodes_visited,
            "leaves_evaluated": self.leaves_evaluated,
            "cutoffs": self.cutoffs,
            "pruned_branches": self.pruned_branches,
            "max_depth": self.max_depth_reached,
        }
        self.record(
            AlgorithmEvent(
                iteration=len(self.events),
                event_type="MOVE_SELECTED",
                current_node=self.root.node_id,
                metrics=metrics,
                metadata={"selected_move": selected_move, "node_type": "ROOT"},
            )
        )
        self.record(
            AlgorithmEvent(
                iteration=len(self.events),
                event_type="COMPLETED",
                current_node=self.root.node_id,
                metrics=metrics,
                metadata={"selected_move": selected_move, "node_type": "ROOT"},
            )
        )
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])


# Short aliases are useful to callers that do not need to distinguish the
# implementation name from the algorithm family.
MinimaxEngine = MinimaxAlphaBetaEngine
AlphaBetaEngine = MinimaxAlphaBetaEngine
AlphaBetaConfig = MinimaxConfig
MinimaxAlphaBetaConfig = MinimaxConfig
DeterministicTreeConfig = TreeGenerationConfig
TreeConfig = TreeGenerationConfig
GameTreeNode = SearchTreeNode
generate_tree = generate_search_tree


StateT = TypeVar("StateT")
MoveT = TypeVar("MoveT")


class GameAdapter(Protocol[StateT, MoveT]):
    def legal_moves(self, state: StateT) -> list[MoveT]: ...
    def apply_move(self, state: StateT, move: MoveT, player: str) -> StateT: ...
    def terminal(self, state: StateT) -> str | None: ...
    def evaluate(self, state: StateT, root_player: str, outcome: str | None, remaining_depth: int) -> float: ...
    def key(self, state: StateT) -> str: ...


class GameSearchEngine(AlgorithmEngine[BaseModel], Generic[StateT, MoveT]):
    """Reusable alpha-beta driver for finite, turn-based games."""

    def __init__(self, config: BaseModel, game: GameAdapter[StateT, MoveT], initial_state: StateT, opponent: str) -> None:
        super().__init__(config)
        self.game = game
        self.initial_state = initial_state
        self.root_player = str(getattr(config, "player", "X"))
        self.opponent = opponent
        self.nodes_visited = self.leaves_evaluated = self.cutoffs = self.pruned_branches = 0
        self.max_depth_reached = 0
        self.selected_move: MoveT | None = None
        self.value = 0.0

    def _event(self, event_type: str, state: StateT, depth: int, *, node_type: str, alpha: float, beta: float, **metadata: Any) -> None:
        self.record(
            AlgorithmEvent(
                iteration=len(self.events),
                event_type=event_type,
                current_node=self.game.key(state),
                metrics={
                    "nodes_visited": self.nodes_visited,
                    "leaves_evaluated": self.leaves_evaluated,
                    "cutoffs": self.cutoffs,
                    "pruned_branches": self.pruned_branches,
                    "depth": depth,
                    "alpha": None if math.isinf(alpha) else alpha,
                    "beta": None if math.isinf(beta) else beta,
                },
                metadata={"node_type": node_type, "alpha": None if math.isinf(alpha) else alpha, "beta": None if math.isinf(beta) else beta, **metadata},
            )
        )

    def _search(self, state: StateT, depth: int, turn: str, alpha: float, beta: float) -> float:
        self.nodes_visited += 1
        self.max_depth_reached = max(self.max_depth_reached, depth)
        terminal = self.game.terminal(state)
        moves = self.game.legal_moves(state) if terminal is None else []
        horizon = depth >= int(getattr(self.config, "max_depth", 0))
        self._event("TRAVERSAL", state, depth, node_type="MAX" if turn == self.root_player else "MIN", alpha=alpha, beta=beta, turn=turn)
        if terminal is not None or horizon or not moves:
            self.leaves_evaluated += 1
            value = self.game.evaluate(state, self.root_player, terminal or ("draw" if not moves else None), int(getattr(self.config, "max_depth", 0)) - depth)
            self._event("NODE_EVALUATED", state, depth, node_type="TERMINAL" if terminal or not moves else "HORIZON", alpha=alpha, beta=beta, value=value, outcome=terminal)
            return value
        maximizing = turn == self.root_player
        best = -math.inf if maximizing else math.inf
        for index, move in enumerate(moves):
            child = self.game.apply_move(state, move, turn)
            value = self._search(child, depth + 1, self.opponent if turn == self.root_player else self.root_player, alpha, beta)
            if maximizing:
                best = max(best, value)
                alpha = max(alpha, best)
            else:
                best = min(best, value)
                beta = min(beta, best)
            self._event("ALPHA_BETA", state, depth, node_type="MAX" if maximizing else "MIN", alpha=alpha, beta=beta, value=best, move=move)
            if bool(getattr(self.config, "alpha_beta", True)) and alpha >= beta:
                remaining = len(moves) - index - 1
                if remaining:
                    self.cutoffs += 1
                    self.pruned_branches += remaining
                    self._event("CUTOFF", state, depth, node_type="MAX" if maximizing else "MIN", alpha=alpha, beta=beta, move=move, pruned_count=remaining)
                    for pruned_move in moves[index + 1 :]:
                        self._event("PRUNED_BRANCH", state, depth, node_type="PRUNED", alpha=alpha, beta=beta, move=pruned_move, parent_move=move)
                break
        return best

    def run(self) -> AlgorithmResult:
        self.events = []
        self.nodes_visited = self.leaves_evaluated = self.cutoffs = self.pruned_branches = 0
        self.max_depth_reached = 0
        self.selected_move = None
        self.record(AlgorithmEvent(iteration=0, event_type="INITIALIZED", current_node=self.game.key(self.initial_state), metadata={"strategy": "minimax", "alpha_beta": bool(getattr(self.config, "alpha_beta", True))}))
        self.value = self._search(self.initial_state, 0, self.root_player, -math.inf, math.inf)
        moves = self.game.legal_moves(self.initial_state)
        if moves:
            # Evaluate each root move with the same deterministic tie-breaking as
            # the recursive search, while keeping the main trace single-pass.
            best_value = -math.inf
            for move in moves:
                child = self.game.apply_move(self.initial_state, move, self.root_player)
                candidate = self.game.evaluate(child, self.root_player, self.game.terminal(child), int(getattr(self.config, "max_depth", 0)) - 1) if int(getattr(self.config, "max_depth", 0)) <= 1 else None
                if candidate is None:
                    # A shallow, side-effect-free helper gives root move ordering
                    # without adding duplicate events to the public trace.
                    candidate = self._score_without_events(child, 1, self.opponent, -math.inf, math.inf)
                if candidate > best_value:
                    best_value, self.selected_move = candidate, move
        metrics = {"value": self.value, "nodes_visited": self.nodes_visited, "leaves_evaluated": self.leaves_evaluated, "cutoffs": self.cutoffs, "pruned_branches": self.pruned_branches, "max_depth": self.max_depth_reached}
        self.record(AlgorithmEvent(iteration=len(self.events), event_type="MOVE_SELECTED", current_node=self.game.key(self.initial_state), metrics=metrics, metadata={"selected_move": self.selected_move, "node_type": "ROOT"}))
        outcome = self.game.terminal(self.initial_state)
        self.record(AlgorithmEvent(iteration=len(self.events), event_type="COMPLETED", current_node=self.game.key(self.initial_state), metrics=metrics, metadata={"selected_move": self.selected_move, "outcome": outcome or "in-progress", "node_type": "ROOT"}))
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])

    def _score_without_events(self, state: StateT, depth: int, turn: str, alpha: float, beta: float) -> float:
        terminal = self.game.terminal(state)
        moves = self.game.legal_moves(state) if terminal is None else []
        max_depth = int(getattr(self.config, "max_depth", 0))
        if terminal is not None or depth >= max_depth or not moves:
            return self.game.evaluate(state, self.root_player, terminal or ("draw" if not moves else None), max_depth - depth)
        maximizing = turn == self.root_player
        best = -math.inf if maximizing else math.inf
        for move in moves:
            child_value = self._score_without_events(state=self.game.apply_move(state, move, turn), depth=depth + 1, turn=self.opponent if maximizing else self.root_player, alpha=alpha, beta=beta)
            if maximizing:
                best, alpha = max(best, child_value), max(alpha, best)
            else:
                best, beta = min(best, child_value), min(beta, best)
            if bool(getattr(self.config, "alpha_beta", True)) and alpha >= beta:
                break
        return best
