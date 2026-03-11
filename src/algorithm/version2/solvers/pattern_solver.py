from __future__ import annotations

from typing import List, Optional

from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.domain.pattern import Pattern
from src.algorithm.version2.domain.pattern_solver_result import PatternSolveResult
from src.algorithm.version2.domain.resources import Resources


class PatternSolver:
    """
    Improved greedy solver.

    Main ideas:
    - Re-score patterns against the current remaining demand each iteration
    - Reward useful coverage
    - Penalize oversupply
    - Penalize poor rack utilization and unnecessary rack growth

    This is still heuristic, but significantly stronger than simple static greedy.
    """

    def __init__(self, patterns: List[Pattern]):
        self.patterns = patterns

    def solve(self, demand: DemandVector) -> PatternSolveResult:
        remaining = DemandVector(
            pc=demand.pc,
            switch=demand.switch,
            router=demand.router,
            controller=demand.controller,
        )

        provided = DemandVector(pc=0, switch=0, router=0, controller=0)
        used_resources = Resources()
        total_capacity = Resources()

        rack_count = 0
        pattern_usage: list[dict] = []

        while not remaining.is_zero():
            best_pattern = self._select_best_pattern(remaining)

            if best_pattern is None:
                break

            multiplicity = self._compute_multiplicity(best_pattern.counts, remaining)

            if multiplicity <= 0:
                break

            used_counts = best_pattern.counts.scale(multiplicity)

            provided = provided + used_counts
            remaining = (remaining - used_counts).clamp_non_negative()

            used_resources += best_pattern.total_resources * multiplicity
            total_capacity += best_pattern.bin_capacity * multiplicity

            rack_count += multiplicity

            pattern_usage.append({
                "pattern": best_pattern.signature(),
                "bin_type": best_pattern.bin_type,
                "count": multiplicity,
                "pattern_counts": best_pattern.counts.as_dict(),
                "used_counts": used_counts.as_dict(),
                "pattern_resources": {
                    "u": best_pattern.total_resources.u,
                    "watt": best_pattern.total_resources.watt,
                    "cost": best_pattern.total_resources.cost,
                    "ports": best_pattern.total_resources.ports,
                },
                "bin_capacity": {
                    "u": best_pattern.bin_capacity.u,
                    "watt": best_pattern.bin_capacity.watt,
                    "cost": best_pattern.bin_capacity.cost,
                    "ports": best_pattern.bin_capacity.ports,
                },
            })

        waste_breakdown = self._compute_waste_breakdown(
            demand=demand,
            provided=provided,
            used_resources=used_resources,
            total_capacity=total_capacity,
            rack_count=rack_count,
        )

        return PatternSolveResult(
            rack_count=rack_count,
            waste_score=waste_breakdown["total_waste_score"],
            remaining=remaining,
            pattern_usage=pattern_usage,
            provided=provided,
            used_resources=used_resources,
            total_capacity=total_capacity,
            waste_breakdown=waste_breakdown,
        )

    def _select_best_pattern(self, remaining: DemandVector) -> Optional[Pattern]:
        best_pattern: Optional[Pattern] = None
        best_score = float("-inf")

        for pattern in self.patterns:
            score = self._pattern_fit_score(pattern, remaining)
            if score > best_score:
                best_score = score
                best_pattern = pattern

        if best_pattern is None or best_score <= 0:
            return None

        return best_pattern

    def _pattern_fit_score(self, pattern: Pattern, remaining: DemandVector) -> float:
        """
        Score a pattern against the current remaining demand.

        Positive signals:
        - useful coverage
        - covering multiple needed dimensions
        - better rack utilization

        Negative signals:
        - oversupply
        - very low rack fill
        """
        counts = pattern.counts

        useful_pc = min(counts.pc, remaining.pc)
        useful_switch = min(counts.switch, remaining.switch)
        useful_router = min(counts.router, remaining.router)
        useful_controller = min(counts.controller, remaining.controller)

        over_pc = max(counts.pc - remaining.pc, 0)
        over_switch = max(counts.switch - remaining.switch, 0)
        over_router = max(counts.router - remaining.router, 0)
        over_controller = max(counts.controller - remaining.controller, 0)

        useful_score = (
            useful_pc * 1.0 +
            useful_switch * 2.0 +
            useful_router * 3.0 +
            useful_controller * 4.0
        )

        oversupply_penalty = (
            over_pc * 1.0 +
            over_switch * 2.0 +
            over_router * 3.0 +
            over_controller * 4.0
        )

        covered_dimensions = sum([
            1 if useful_pc > 0 else 0,
            1 if useful_switch > 0 else 0,
            1 if useful_router > 0 else 0,
            1 if useful_controller > 0 else 0,
        ])

        dimension_bonus = covered_dimensions * 0.35

        util = pattern.utilization_ratios()
        utilization_score = (
            util["u"] * 2.0 +
            util["watt"] * 1.2 +
            util["ports"] * 1.5
        )

        total_utilization = (util["u"] + util["watt"] + util["ports"]) / 3.0
        low_fill_penalty = 0.0
        if total_utilization < 0.35:
            low_fill_penalty = (0.35 - total_utilization) * 3.0

        return (
            useful_score +
            dimension_bonus +
            utilization_score -
            oversupply_penalty * 1.25 -
            low_fill_penalty
        )

    def _compute_multiplicity(self, pattern_counts: DemandVector, remaining: DemandVector) -> int:
        """
        Compute the safest multiplicity.

        If we can take the pattern multiple times without oversupplying
        the dimensions it covers, take the max safe multiplicity.
        Otherwise allow a single use only when it is still reasonable.
        """
        bounds = []

        if pattern_counts.pc > 0 and remaining.pc > 0:
            bounds.append(remaining.pc // pattern_counts.pc)

        if pattern_counts.switch > 0 and remaining.switch > 0:
            bounds.append(remaining.switch // pattern_counts.switch)

        if pattern_counts.router > 0 and remaining.router > 0:
            bounds.append(remaining.router // pattern_counts.router)

        if pattern_counts.controller > 0 and remaining.controller > 0:
            bounds.append(remaining.controller // pattern_counts.controller)

        positive_bounds = [b for b in bounds if b > 0]
        if positive_bounds:
            return min(positive_bounds)

        if self._is_reasonable_single_use(pattern_counts, remaining):
            return 1

        return 0

    def _is_reasonable_single_use(self, pattern_counts: DemandVector, remaining: DemandVector) -> bool:
        useful_score = (
            min(pattern_counts.pc, remaining.pc) * 1.0 +
            min(pattern_counts.switch, remaining.switch) * 2.0 +
            min(pattern_counts.router, remaining.router) * 3.0 +
            min(pattern_counts.controller, remaining.controller) * 4.0
        )

        oversupply_score = (
            max(pattern_counts.pc - remaining.pc, 0) * 1.0 +
            max(pattern_counts.switch - remaining.switch, 0) * 2.0 +
            max(pattern_counts.router - remaining.router, 0) * 3.0 +
            max(pattern_counts.controller - remaining.controller, 0) * 4.0
        )

        return useful_score > 0 and oversupply_score <= useful_score

    def _compute_waste_breakdown(
        self,
        demand: DemandVector,
        provided: DemandVector,
        used_resources: Resources,
        total_capacity: Resources,
        rack_count: int,
    ) -> dict:
        """
        Composite waste metric.

        Includes:
        - oversupply of components
        - unused rack capacity
        - penalty for opening many racks
        """
        oversupply = DemandVector(
            pc=max(provided.pc - demand.pc, 0),
            switch=max(provided.switch - demand.switch, 0),
            router=max(provided.router - demand.router, 0),
            controller=max(provided.controller - demand.controller, 0),
        )

        item_oversupply_score = (
            oversupply.pc * 1.0 +
            oversupply.switch * 2.0 +
            oversupply.router * 3.0 +
            oversupply.controller * 4.0
        )

        unused_u = max(total_capacity.u - used_resources.u, 0)
        unused_watt = max(total_capacity.watt - used_resources.watt, 0)
        unused_ports = max(total_capacity.ports - used_resources.ports, 0)
        unused_cost_capacity = max(total_capacity.cost - used_resources.cost, 0)

        u_util = (used_resources.u / total_capacity.u) if total_capacity.u else 0.0
        watt_util = (used_resources.watt / total_capacity.watt) if total_capacity.watt else 0.0
        ports_util = (used_resources.ports / total_capacity.ports) if total_capacity.ports else 0.0

        u_waste_ratio = 1.0 - u_util if total_capacity.u else 0.0
        watt_waste_ratio = 1.0 - watt_util if total_capacity.watt else 0.0
        ports_waste_ratio = 1.0 - ports_util if total_capacity.ports else 0.0

        resource_waste_score = (
            u_waste_ratio * 40.0 +
            watt_waste_ratio * 25.0 +
            ports_waste_ratio * 35.0
        )

        rack_penalty_score = max(rack_count - 1, 0) * 5.0

        total_waste_score = (
            item_oversupply_score +
            resource_waste_score +
            rack_penalty_score
        )

        return {
            "oversupply": oversupply.as_dict(),
            "unused_capacity": {
                "u": unused_u,
                "watt": unused_watt,
                "ports": unused_ports,
                "cost_capacity": unused_cost_capacity,
            },
            "utilization": {
                "u": round(u_util, 4),
                "watt": round(watt_util, 4),
                "ports": round(ports_util, 4),
            },
            "item_oversupply_score": round(item_oversupply_score, 4),
            "resource_waste_score": round(resource_waste_score, 4),
            "rack_penalty_score": round(rack_penalty_score, 4),
            "total_waste_score": round(total_waste_score, 4),
        }