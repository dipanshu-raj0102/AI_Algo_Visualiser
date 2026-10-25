from __future__ import annotations

from copy import deepcopy

from pydantic import Field

from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult
from .game_search import MinimaxAlphaBetaEngine, MinimaxConfig, SearchTreeNode, generate_search_tree


class MoveOrderingConfig(MinimaxConfig):
    depth: int = Field(default=4, ge=1, le=8)
    branching_factor: int = Field(default=3, ge=2, le=8)


def _leaf_hint(node: SearchTreeNode) -> float:
    if node.is_leaf:
        return float(node.value or 0)
    return sum(_leaf_hint(child) for child in node.children) / len(node.children)


def _reorder(node: SearchTreeNode, good: bool) -> SearchTreeNode:
    if node.is_leaf:
        return node
    children = [_reorder(child, good) for child in node.children]
    children.sort(key=_leaf_hint, reverse=good)
    return SearchTreeNode(node_id=node.node_id, children=tuple(children), value=node.value)


class MoveOrderingImpactEngine(AlgorithmEngine[MoveOrderingConfig]):
    algorithm_id = "alpha-beta-move-ordering"

    def run(self) -> AlgorithmResult:
        source = generate_search_tree(self.config)
        runs: list[dict[str, object]] = []
        for label, good in (("good-ordering", True), ("bad-ordering", False)):
            result = MinimaxAlphaBetaEngine(self.config, root=_reorder(deepcopy(source), good)).run()
            final = result.final_state
            summary = {"label": label, "nodes_visited": final.metrics.get("nodes_visited", 0), "pruned_branches": final.metrics.get("pruned_branches", 0), "cutoffs": final.metrics.get("cutoffs", 0), "events": len(result.events)}
            runs.append(summary)
            self.record(AlgorithmEvent(iteration=len(self.events), event_type="STATE_EVALUATED", metrics={key: value for key, value in summary.items() if isinstance(value, (int, float, str))}, metadata={"ordering": label, "trace": [event.model_dump() for event in result.events]}))
        self.record(AlgorithmEvent(iteration=len(self.events), event_type="COMPLETED", metrics={"runs": len(runs)}, metadata={"runs": runs, "tree": "same-seeded-tree"}))
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])
