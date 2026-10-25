from __future__ import annotations

import heapq
import math
from itertools import count
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .base import AlgorithmEngine, AlgorithmEvent, AlgorithmResult


class City(BaseModel):
    name: str
    x: float
    y: float


class CityMapConfig(BaseModel):
    cities: list[City] = Field(default_factory=lambda: [City(name="A", x=0, y=0), City(name="B", x=2, y=1), City(name="C", x=4, y=0), City(name="D", x=4, y=3), City(name="E", x=7, y=2)])
    roads: list[tuple[str, str, float]] = Field(default_factory=lambda: [("A", "B", 2.2), ("A", "C", 4.5), ("B", "C", 2.1), ("B", "D", 3.0), ("C", "D", 3.2), ("D", "E", 3.1), ("C", "E", 5.8)])
    start: str = "A"
    goal: str = "E"

    @model_validator(mode="after")
    def validate_graph(self) -> "CityMapConfig":
        names = {city.name for city in self.cities}
        if self.start not in names or self.goal not in names or self.start == self.goal:
            raise ValueError("start and goal must be distinct city names")
        if any(left not in names or right not in names or cost <= 0 for left, right, cost in self.roads):
            raise ValueError("roads must reference known cities and have positive costs")
        return self


class CityMapAStarEngine(AlgorithmEngine[CityMapConfig]):
    algorithm_id = "astar-city-map"

    def run(self) -> AlgorithmResult:
        cities = {city.name: city for city in self.config.cities}
        graph: dict[str, list[tuple[str, float]]] = {name: [] for name in cities}
        for left, right, cost in self.config.roads:
            graph[left].append((right, cost)); graph[right].append((left, cost))
        h = lambda node: math.dist((cities[node].x, cities[node].y), (cities[self.config.goal].x, cities[self.config.goal].y))
        parents: dict[str, str | None] = {self.config.start: None}; g = {self.config.start: 0.0}; frontier = {self.config.start: (h(self.config.start), 0.0, h(self.config.start))}; explored: set[str] = set(); queue: list[tuple[float, int, str]] = [(h(self.config.start), next(count()), self.config.start)]
        counter = count(); queue = [(h(self.config.start), next(counter), self.config.start)]
        expanded = 0
        self.record(AlgorithmEvent(iteration=0, event_type="INITIALIZED", current_node=self.config.start, frontier=[{"node": self.config.start, "g": 0, "h": h(self.config.start), "f": h(self.config.start)}], metadata={"cities": [city.model_dump() for city in self.config.cities], "roads": self.config.roads, "start": self.config.start, "goal": self.config.goal}))
        while queue:
            _, _, current = heapq.heappop(queue)
            if current not in frontier: continue
            del frontier[current]; explored.add(current); expanded += 1
            path = self._path(parents, current)
            if current == self.config.goal:
                metrics = {"nodes_expanded": expanded, "path_cost": g[current], "path_length": len(path)}
                self.record(AlgorithmEvent(iteration=len(self.events), event_type="SOLUTION_FOUND", current_node=current, explored=sorted(explored), path=path, metrics=metrics, metadata={"message": "A* selected the city with the lowest estimated total route cost."}))
                self.record(AlgorithmEvent(iteration=len(self.events), event_type="COMPLETED", current_node=current, explored=sorted(explored), path=path, metrics=metrics))
                return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])
            for neighbour, cost in graph[current]:
                tentative = g[current] + cost
                if neighbour in explored and tentative >= g.get(neighbour, math.inf): continue
                if tentative < g.get(neighbour, math.inf):
                    parents[neighbour] = current; g[neighbour] = tentative; hn = h(neighbour); fn = tentative + hn; frontier[neighbour] = (fn, tentative, hn); heapq.heappush(queue, (fn, next(counter), neighbour))
            self.record(AlgorithmEvent(iteration=len(self.events), event_type="NODE_EXPANDED", current_node=current, frontier=[{"node": n, "g": v[1], "h": v[2], "f": v[0]} for n, v in frontier.items()], explored=sorted(explored), path=path, metrics={"nodes_expanded": expanded}, metadata={"g": g[current], "h": h(current), "f": g[current] + h(current)}))
        self.record(AlgorithmEvent(iteration=len(self.events), event_type="FAILED", metrics={"nodes_expanded": expanded}, metadata={"message": "No route exists."}))
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="failed", events=self.events, final_state=self.events[-1])

    @staticmethod
    def _path(parents: dict[str, str | None], node: str) -> list[str]:
        path = []; current: str | None = node
        while current is not None: path.append(current); current = parents.get(current)
        return list(reversed(path))


class Page(BaseModel):
    relevance: float = Field(ge=0, le=1)
    links: list[str] = Field(default_factory=list)


class WebCrawlerConfig(BaseModel):
    pages: dict[str, Page] = Field(default_factory=lambda: {"home": Page(relevance=.6, links=["docs", "blog"]), "docs": Page(relevance=.95, links=["api", "home"]), "blog": Page(relevance=.7, links=["home"]), "api": Page(relevance=1.0)})
    start: str = "home"
    max_pages: int = Field(default=10, ge=1, le=100)


class WebCrawlerBestFirstEngine(AlgorithmEngine[WebCrawlerConfig]):
    algorithm_id = "web-crawler-best-first"

    def run(self) -> AlgorithmResult:
        queue: list[tuple[float, int, str]] = []; counter = count(); heapq.heappush(queue, (-self.config.pages[self.config.start].relevance, next(counter), self.config.start)); visited: list[str] = []
        self.record(AlgorithmEvent(iteration=0, event_type="INITIALIZED", current_node=self.config.start, metadata={"pages": {key: page.model_dump() for key, page in self.config.pages.items()}, "strategy": "relevance"}))
        while queue and len(visited) < self.config.max_pages:
            _, _, page = heapq.heappop(queue)
            if page in visited: continue
            visited.append(page); score = self.config.pages[page].relevance
            for link in self.config.pages[page].links:
                if link in self.config.pages and link not in visited: heapq.heappush(queue, (-self.config.pages[link].relevance, next(counter), link))
            self.record(AlgorithmEvent(iteration=len(self.events), event_type="NODE_EXPANDED", current_node=page, explored=visited, frontier=[{"node": item[2], "relevance": -item[0]} for item in queue], metrics={"pages_visited": len(visited), "frontier_size": len(queue)}, metadata={"relevance": score, "message": "The crawler prioritizes the most relevant page in its frontier."}))
        self.record(AlgorithmEvent(iteration=len(self.events), event_type="COMPLETED", explored=visited, metrics={"pages_visited": len(visited)}, metadata={"visit_order": visited}))
        return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])


class LandmarkRouteConfig(CityMapConfig):
    pass


class LandmarkRouteEngine(CityMapAStarEngine):
    algorithm_id = "landmark-best-first"

    def run(self) -> AlgorithmResult:
        # The same graph contract is intentionally used, but frontier priority is h(n) only.
        original = self.config
        cities = {city.name: city for city in original.cities}; graph: dict[str, list[tuple[str, float]]] = {name: [] for name in cities}
        for left, right, cost in original.roads: graph[left].append((right, cost)); graph[right].append((left, cost))
        h = lambda node: math.dist((cities[node].x, cities[node].y), (cities[original.goal].x, cities[original.goal].y)); parents: dict[str, str | None] = {original.start: None}; costs = {original.start: 0.0}; queue = [(h(original.start), 0, original.start)]; visited = set(); self.record(AlgorithmEvent(iteration=0, event_type="INITIALIZED", current_node=original.start, metadata={"cities": [city.model_dump() for city in original.cities], "roads": original.roads, "start": original.start, "goal": original.goal, "strategy": "landmark-heuristic"}))
        while queue:
            _, _, current = heapq.heappop(queue)
            if current in visited: continue
            visited.add(current); path = self._path(parents, current)
            if current == original.goal:
                metrics = {"nodes_expanded": len(visited), "path_cost": costs[current], "path_length": len(path)}; self.record(AlgorithmEvent(iteration=len(self.events), event_type="COMPLETED", current_node=current, explored=sorted(visited), path=path, metrics=metrics, metadata={"message": "Greedy landmark routing reached the destination."})); return AlgorithmResult(algorithm_id=self.algorithm_id, status="completed", events=self.events, final_state=self.events[-1])
            for neighbour, cost in graph[current]:
                if neighbour not in visited:
                    if neighbour not in parents:
                        parents[neighbour] = current
                    costs[neighbour] = min(costs.get(neighbour, math.inf), costs[current] + cost)
                    heapq.heappush(queue, (h(neighbour), len(self.events), neighbour))
            self.record(AlgorithmEvent(iteration=len(self.events), event_type="NODE_EXPANDED", current_node=current, explored=sorted(visited), path=path, metrics={"nodes_expanded": len(visited), "path_cost": costs[current]}, metadata={"h": h(current)}))
        self.record(AlgorithmEvent(iteration=len(self.events), event_type="FAILED", explored=sorted(visited))); return AlgorithmResult(algorithm_id=self.algorithm_id, status="failed", events=self.events, final_state=self.events[-1])
