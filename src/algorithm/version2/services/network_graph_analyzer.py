from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Any


class NetworkGraphAnalyzer:
    def analyze(
        self,
        links: List[Dict[str, Any]],
    ) -> Dict[str, float]:

        adjacency = self._build_adjacency(
            links
        )

        connectivity_score = (
            self._connectivity_score(
                adjacency
            )
        )

        diameter_score = (
            self._diameter_score(
                adjacency
            )
        )

        bottleneck_penalty = (
            self._centralization_penalty(
                adjacency
            )
        )

        degree_balance_score = (
            self._degree_balance_score(
                adjacency
            )
        )
        resilience_score = (
            self._resilience_score(
                adjacency
            )
        )
        edge_count = len(links)
        node_count = len(adjacency)

        return {
            "connectivity_score":
                connectivity_score,
            "diameter_score":
                diameter_score,
            "centralization_penalty":
                bottleneck_penalty,
            "degree_balance_score":
                degree_balance_score,
            "resilience_score":
                resilience_score,
            "edge_count":
                edge_count,
            "node_count":
                node_count,
        }

    def _build_adjacency(
        self,
        links: List[Dict[str, Any]],
    ) -> Dict[str, Set[str]]:

        adjacency: Dict[str, Set[str]] = {}

        for link in links:
            a = link["from"]["node_id"]
            b = link["to"]["node_id"]

            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)

        return adjacency

    def _connectivity_score(
        self,
        adjacency: Dict[str, Set[str]],
    ) -> float:

        if not adjacency:
            return 0.0

        start = next(iter(adjacency))

        visited = self._bfs(start, adjacency)

        connected_ratio = len(visited) / len(adjacency)

        return self._clamp01(connected_ratio)

    def _degree_balance_score(
        self,
        adjacency: Dict[str, Set[str]],
    ) -> float:

        if not adjacency:
            return 0.0

        degrees = [
            len(neighbors)
            for neighbors in adjacency.values()
        ]

        avg_degree = sum(degrees) / len(degrees)

        imbalance = (
            sum(abs(d - avg_degree) for d in degrees)
            / len(degrees)
        )

        normalized_imbalance = imbalance / max(avg_degree, 1)

        return self._clamp01(
            1.0 - normalized_imbalance
        )

    def _centralization_penalty(
        self,
        adjacency: Dict[str, Set[str]],
    ) -> float:

        if not adjacency:
            return 0.0

        degrees = [
            len(neighbors)
            for neighbors in adjacency.values()
        ]

        avg_degree = (
            sum(degrees) /
            len(degrees)
        )

        variance = (

            sum(
                (d - avg_degree) ** 2
                for d in degrees
            )

            / len(degrees)

        )

        normalized = variance / max(
            avg_degree ** 2,
            1,
        )

        return self._clamp01(
            normalized
        )
    def _diameter_score(
        self,
        adjacency: Dict[str, Set[str]],
    ) -> float:

        if not adjacency:
            return 0.0

        max_distance = 0

        for node in adjacency:
            distances = self._bfs_distances(
                node,
                adjacency,
            )

            if distances:
                max_distance = max(
                    max_distance,
                    max(distances.values()),
                )

        theoretical_max = max(len(adjacency) - 1, 1)

        normalized = max_distance / theoretical_max

        return self._clamp01(
            1.0 - normalized
        )

    def _resilience_score(
        self,
        adjacency: Dict[str, Set[str]],
    ) -> float:

        if len(adjacency) <= 1:
            return 1.0

        surviving_ratios = []

        for failed_node in adjacency.keys():

            modified = {
                n: set(neighbors)
                for n, neighbors in adjacency.items()
                if n != failed_node
            }

            for neighbors in modified.values():
                neighbors.discard(failed_node)

            if not modified:
                surviving_ratios.append(0.0)
                continue

            start = next(iter(modified))

            visited = self._bfs(start, modified)

            ratio = len(visited) / len(modified)

            surviving_ratios.append(ratio)

        avg_survival = (
            sum(surviving_ratios)
            / len(surviving_ratios)
        )

        return self._clamp01(avg_survival)

    def _bfs(
        self,
        start: str,
        adjacency: Dict[str, Set[str]],
    ) -> Set[str]:

        visited = set()

        queue = deque([start])

        while queue:
            node = queue.popleft()

            if node in visited:
                continue

            visited.add(node)

            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        return visited

    def _bfs_distances(
        self,
        start: str,
        adjacency: Dict[str, Set[str]],
    ) -> Dict[str, int]:

        distances = {
            start: 0
        }

        queue = deque([start])

        while queue:
            node = queue.popleft()

            for neighbor in adjacency.get(node, []):

                if neighbor in distances:
                    continue

                distances[neighbor] = (
                    distances[node] + 1
                )

                queue.append(neighbor)

        return distances

    def _clamp01(
        self,
        value: float,
    ) -> float:

        return max(
            0.0,
            min(1.0, value),
        )