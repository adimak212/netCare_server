from __future__ import annotations

from typing import Any, Dict, List, Tuple
import traceback
from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.domain.pattern_solver_result import (
    PatternSolveResult,
)

from src.algorithm.version2.services.links import (
    build_links,
)

from src.algorithm.version2.services.build_nodes import (
    build_nodes,
)

from src.algorithm.version2.services.network_graph_analyzer import (
    NetworkGraphAnalyzer,
)

from src.algorithm.version2.solvers.pattern_generator import (
    PatternGenerator,
)

from src.algorithm.version2.solvers.beam_solver import (
    BeamPatternSolver,
)

from src.algorithm.version2.services.topology_evaluator import (
    TopologyEvaluator,
)

from src.algorithm.version2.topologies.fat_tree import (
    FatTreeTopology,
)

from src.algorithm.version2.topologies.fnn import (
    FNNTopology,
)

from src.algorithm.version2.topologies.mesh import (
    MeshTopology,
)

from src.algorithm.version2.topologies.sdn import (
    SDNTopology,
)

from src.algorithm.version2.topologies.hybrid import (
    HybridTopology,
)


class TopologyRanker:

    def __init__(
        self,
        templates,
        bin_templates,
    ):

        self.templates = templates
        self.benefit_lambda = 0.4
        self.bin_templates = bin_templates

        self.templates = self._normalize_templates(
            templates
        )

        self.pattern_generator = PatternGenerator(
            templates=self.templates,
            bin_templates=self.bin_templates,
        )

        self.evaluator = TopologyEvaluator(
            rack_cost_weight=1.0,
            waste_cost_weight=1.0,
            equipment_cost_weight=0.001,
        )

        self.graph_analyzer = (
            NetworkGraphAnalyzer()
        )

        self.topologies = [
            FatTreeTopology(),
            FNNTopology(),
            MeshTopology(),
            SDNTopology(),
            HybridTopology(),
        ]

        self._solve_cache: Dict[
            Tuple,
            PatternSolveResult
        ] = {}

        self._patterns_cache: Dict[
            str,
            list
        ] = {}

    def rank(
        self,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        params = payload["params"]

        preferences = payload["preferences"]

        unit_costs = payload["unit_costs"]

        results: List[Dict[str, Any]] = []

        for topology in self.topologies:

            try:

                normalized = topology.normalize(
                    params
                )

                items = topology.build_items(
                    normalized,
                    self.templates,
                )

                nodes = build_nodes(items)

                links = build_links(
                    nodes,
                    topology.key,
                )

                graph_metrics = (
                    self.graph_analyzer.analyze(
                        links
                    )
                )

                demand = (
                    topology.to_pattern_demand(
                        normalized
                    )
                )

                solve_result = (
                    self._solve_for_demand(
                        topology.key,
                        params,
                        normalized,
                        demand,
                    )
                )

                topology_metrics = (
                    self._get_topology_metrics(
                        topology
                    )
                )

                topology_metrics.update(
                    graph_metrics
                )

                evaluation = (
                    self.evaluator.evaluate(
                        topology.key,
                        topology.name,
                        demand,
                        preferences,
                        topology_metrics,
                        unit_costs,
                        solve_result.rack_count,
                        solve_result.waste_score,
                    )
                )

                results.append({
                    "key": topology.key,
                    "name": topology.name,
                    "normalized": normalized,
                    "demand": demand.as_dict(),
                    "solve_result": solve_result,
                    "evaluation": evaluation,
                    "final_score": (
                        evaluation.final_score
                    ),
                    "waste": (
                        solve_result.waste_score
                    ),
                    "waste_breakdown": getattr(
                        solve_result,
                        "waste_breakdown",
                        {},
                    ),
                    "rack_count": (
                        solve_result.rack_count
                    ),
                    "links": links,
                    "graph_metrics": (
                        graph_metrics
                    ),
                })

            except Exception as exc:
                results.append({
                    "key": getattr(
                        topology,
                        "key",
                        "unknown",
                    ),

                    "name": getattr(
                        topology,
                        "name",
                        "Unknown",
                    ),

                    "error": str(exc),

                    "traceback": traceback.format_exc(),

                    "final_score": float("-inf"),
                })

        results.sort(
            key=lambda x: x["final_score"],
            reverse=True,
        )

        return results

    def _solve_for_demand(
        self,
        topology_key: str,
        params: Dict[str, Any],
        normalized: Dict[str, Any],
        demand: DemandVector,
    ) -> PatternSolveResult:

        cache_key = self._make_cache_key(
            topology_key,
            params,
            normalized,
            demand,
        )

        if cache_key in self._solve_cache:
            return self._solve_cache[
                cache_key
            ]

        patterns = self._get_all_patterns()

        solver = BeamPatternSolver(
            patterns,
            beam_width=5,
        )

        solve_result = solver.solve(
            demand
        )   

        self._solve_cache[
            cache_key
        ] = solve_result

        return solve_result

    def _get_all_patterns(
        self,
    ) -> list:

        all_patterns = []

        for bin_type in (
            self.bin_templates.keys()
        ):

            if (
                bin_type
                not in self._patterns_cache
            ):

                self._patterns_cache[
                    bin_type
                ] = (
                    self.pattern_generator
                    .generate_for_bin_type(
                        bin_type
                    )
                )

            all_patterns.extend(
                self._patterns_cache[
                    bin_type
                ]
            )

        return all_patterns

    def _make_cache_key(
        self,
        topology_key: str,
        params: Dict[str, Any],
        normalized: Dict[str, Any],
        demand: DemandVector,
    ) -> Tuple:

        return (
            topology_key,

            tuple(sorted(
                (str(k), str(v))
                for k, v in params.items()
            )),

            tuple(sorted(
                (str(k), str(v))
                for k, v in normalized.items()
            )),

            tuple(sorted(
                (str(k), str(v))
                for k, v in demand
                .as_dict()
                .items()
            )),
        )

    def _get_topology_metrics(
        self,
        topology,
    ) -> dict[str, float]:

        if hasattr(
            topology,
            "metrics",
        ):
            return topology.metrics()

        if hasattr(
            topology,
            "get_metrics",
        ):
            return topology.get_metrics()

        if hasattr(
            topology,
            "topology_metrics",
        ):
            return topology.topology_metrics()

        raise AttributeError(
            f"{topology.__class__.__name__} "
            f"has no metrics() "
            f"/ get_metrics() method"
        )

    def _normalize_templates(
        self,
        templates,
    ):

        normalized = dict(templates)

        aliases = {
            "core_router": [
                "router",
            ],

            "agg_switch": [
                "switch",
            ],

            "edge_switch": [
                "switch",
            ],

            "sdn_controller": [
                "controller",
            ],

            "pc": [
                "host",
            ],
        }

        for target, candidates in aliases.items():

            if target in normalized:
                continue

            for candidate in candidates:

                if candidate in normalized:

                    normalized[target] = (
                        normalized[candidate]
                    )

                    break
        return normalized