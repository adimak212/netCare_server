
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import List

from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.domain.pattern import Pattern
from src.algorithm.version2.domain.pattern_solver_result import PatternSolveResult
from src.algorithm.version2.domain.resources import Resources


@dataclass
class BeamState:
    remaining: DemandVector
    provided: DemandVector
    rack_count: int
    used_resources: Resources
    total_capacity: Resources
    pattern_usage: list

    def is_done(self) -> bool:
        return self.remaining.is_zero()


class BeamPatternSolver:

    def __init__(
        self,
        patterns: List[Pattern],
        beam_width: int = 5,
        max_steps: int = 50,
    ):
        self.patterns = patterns
        self.beam_width = beam_width
        self.max_steps = max_steps

        self.coverage_weight = 0.45
        self.rack_penalty_weight = 0.20
        self.waste_penalty_weight = 0.15
        self.future_penalty_weight = 0.20

    def solve(self, demand: DemandVector) -> PatternSolveResult:
        initial_state = BeamState(
            remaining=DemandVector(
                pc=demand.pc,
                switch=demand.switch,
                router=demand.router,
                controller=demand.controller,
            ),
            provided=DemandVector(
                pc=0,
                switch=0,
                router=0,
                controller=0,
            ),
            rack_count=0,
            used_resources=Resources(),
            total_capacity=Resources(),
            pattern_usage=[],
        )

        beam: List[BeamState] = [initial_state]

        for _ in range(self.max_steps):
            new_states: List[BeamState] = []

            for state in beam:
                if state.is_done():
                    new_states.append(state)
                    continue

                for pattern in self.patterns[:10]:
                    multiplicity = self._compute_multiplicity(
                        pattern.counts,
                        state.remaining,
                    )

                    if multiplicity <= 0:
                        continue

                    new_state = self._apply_pattern(
                        state,
                        pattern,
                        multiplicity,
                    )

                    new_states.append(new_state)

            if not new_states:
                break

            new_states.sort(
                key=lambda s: self._score_state(s, demand),
                reverse=True,
            )

            beam = new_states[: self.beam_width]

            if all(state.is_done() for state in beam):
                break

        best_state = max(
            beam,
            key=lambda s: self._score_state(s, demand),
        )

        waste_breakdown = self._compute_waste_breakdown(
            demand=demand,
            provided=best_state.provided,
            used_resources=best_state.used_resources,
            total_capacity=best_state.total_capacity,
            rack_count=best_state.rack_count,
        )

        return PatternSolveResult(
            rack_count=best_state.rack_count,
            waste_score=waste_breakdown["total_waste_score"],
            remaining=best_state.remaining,
            pattern_usage=best_state.pattern_usage,
            provided=best_state.provided,
            used_resources=best_state.used_resources,
            total_capacity=best_state.total_capacity,
            waste_breakdown=waste_breakdown,
        )

    def _apply_pattern(
        self,
        state: BeamState,
        pattern: Pattern,
        multiplicity: int,
    ) -> BeamState:

        new_state = deepcopy(state)

        used_counts = pattern.counts.scale(multiplicity)

        new_state.provided = new_state.provided + used_counts

        new_state.remaining = (
            new_state.remaining - used_counts
        ).clamp_non_negative()

        new_state.used_resources += (
            pattern.total_resources * multiplicity
        )

        new_state.total_capacity += (
            pattern.bin_capacity * multiplicity
        )

        new_state.rack_count += multiplicity

        new_state.pattern_usage.append({
            "pattern": pattern.signature(),
            "bin_type": pattern.bin_type,
            "count": multiplicity,
        })

        return new_state

    def _score_state(
        self,
        state: BeamState,
        demand: DemandVector,
    ) -> float:

        total_demand = max(demand.total_items(), 1)

        provided_items = state.provided.total_items()

        coverage_ratio = self._normalize_ratio(
            provided_items,
            total_demand,
        )

        remaining_items = state.remaining.total_items()

        future_penalty = self._normalize_ratio(
            remaining_items,
            total_demand,
        )

        theoretical_max_racks = max(total_demand, 1)

        rack_penalty = self._normalize_ratio(
            state.rack_count,
            theoretical_max_racks,
        )

        unused_u = max(
            state.total_capacity.u - state.used_resources.u,
            0,
        )

        unused_ports = max(
            state.total_capacity.ports - state.used_resources.ports,
            0,
        )

        total_capacity_measure = max(
            state.total_capacity.u + state.total_capacity.ports,
            1,
        )

        waste_penalty = self._normalize_ratio(
            unused_u + unused_ports,
            total_capacity_measure,
        )

        total_weight = (
            self.coverage_weight +
            self.rack_penalty_weight +
            self.waste_penalty_weight +
            self.future_penalty_weight
        )

        wc = self.coverage_weight / total_weight
        wr = self.rack_penalty_weight / total_weight
        ww = self.waste_penalty_weight / total_weight
        wf = self.future_penalty_weight / total_weight

        final_score = (
            wc * coverage_ratio
            - wr * rack_penalty
            - ww * waste_penalty
            - wf * future_penalty
        )

        return final_score

    def _compute_multiplicity(
        self,
        pattern_counts: DemandVector,
        remaining: DemandVector,
    ) -> int:

        bounds = []

        if pattern_counts.pc > 0 and remaining.pc > 0:
            bounds.append(
                remaining.pc // pattern_counts.pc
            )

        if pattern_counts.switch > 0 and remaining.switch > 0:
            bounds.append(
                remaining.switch // pattern_counts.switch
            )

        if pattern_counts.router > 0 and remaining.router > 0:
            bounds.append(
                remaining.router // pattern_counts.router
            )

        if pattern_counts.controller > 0 and remaining.controller > 0:
            bounds.append(
                remaining.controller // pattern_counts.controller
            )

        positive_bounds = [b for b in bounds if b > 0]

        if positive_bounds:
            return min(positive_bounds)

        if self._is_reasonable_single_use(
            pattern_counts,
            remaining,
        ):
            return 1

        return 0

    def _is_reasonable_single_use(
        self,
        pattern_counts: DemandVector,
        remaining: DemandVector,
    ) -> bool:

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

        return (
            useful_score > 0 and
            oversupply_score <= useful_score
        )

    def _compute_waste_breakdown(
        self,
        demand: DemandVector,
        provided: DemandVector,
        used_resources: Resources,
        total_capacity: Resources,
        rack_count: int,
    ) -> dict:

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

        unused_u = max(
            total_capacity.u - used_resources.u,
            0,
        )

        unused_watt = max(
            total_capacity.watt - used_resources.watt,
            0,
        )

        unused_ports = max(
            total_capacity.ports - used_resources.ports,
            0,
        )

        unused_cost_capacity = max(
            total_capacity.cost - used_resources.cost,
            0,
        )

        u_util = (
            used_resources.u / total_capacity.u
        ) if total_capacity.u else 0.0

        watt_util = (
            used_resources.watt / total_capacity.watt
        ) if total_capacity.watt else 0.0

        ports_util = (
            used_resources.ports / total_capacity.ports
        ) if total_capacity.ports else 0.0

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

    def _normalize_ratio(
        self,
        value: float,
        maximum: float,
    ) -> float:

        if maximum <= 0:
            return 0.0

        normalized = value / maximum

        return max(0.0, min(1.0, normalized))

