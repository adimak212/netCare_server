from __future__ import annotations

import math

from src.algorithm.version2.domain.topology_evaluation import TopologyEvaluation
from src.algorithm.version2.domain.user_preferences import UserPreferences
from src.algorithm.version2.domain.demand_vector import DemandVector


class TopologyEvaluator:
    def __init__(
        self,
        logical_cost_weight: float = 0.20,
        equipment_cost_weight: float = 0.35,
        rack_cost_weight: float = 0.25,
        waste_cost_weight: float = 0.20,
        resource_penalty_weight: float = 0.25,
    ):
        # משקלים פנימיים של cost הוגן
        self.logical_cost_weight = logical_cost_weight
        self.equipment_cost_weight = equipment_cost_weight
        self.rack_cost_weight = rack_cost_weight
        self.waste_cost_weight = waste_cost_weight

        # משקל פנימי קבוע של penalty על יעילות משאבים
        self.resource_penalty_weight = resource_penalty_weight

        # קבועי נרמול
        self.MAX_SCORE_10 = 10.0
        self.MAX_REL_EQUIPMENT_COST = 5000.0
        self.MAX_REL_RACK_COST = 1.0
        self.MAX_REL_WASTE = 2.0
        self.MAX_UTILIZATION_PENALTY = 1.0

        # קיבולת rack לצורך הערכת utilization
        self.RACK_CAPACITY = 40.0

    def _clamp01(self, value: float) -> float:
        return max(0.0, min(float(value), 1.0))

    def compute_equipment_cost(
        self,
        demand: DemandVector,
        unit_costs: dict[str, float],
    ) -> float:
        return (
            demand.pc * unit_costs.get("pc", 0.0) +
            demand.switch * unit_costs.get("switch", 0.0) +
            demand.router * unit_costs.get("router", 0.0) +
            demand.controller * unit_costs.get("controller", 0.0)
        )

    def compute_benefit_score(
        self,
        scalability_norm: float,
        redundancy_norm: float,
    ) -> float:
        """
        כמה תועלת טופולוגית הפתרון נותן.
        גבוה יותר = יותר מצדיק עלות/מורכבות.
        """
        return self._clamp01(
            0.5 * scalability_norm +
            0.5 * redundancy_norm
        )

    def compute_fair_cost_norm(
        self,
        logical_cost_score: float,
        equipment_cost: float,
        rack_count: int,
        waste_score: float,
        demand: DemandVector,
        scalability_norm: float,
        redundancy_norm: float,
    ) -> float:
        """
        cost_norm הוגן:
        לא עלות מוחלטת, אלא עלות יחסית לביקוש,
        ואז התאמה לפי benefit של הטופולוגיה.
        0 = זול/יעיל יחסית
        1 = יקר/לא יעיל יחסית
        """
        demand_size = max(float(demand.total_items()), 1.0)

        logical_norm = self._clamp01(logical_cost_score / self.MAX_SCORE_10)

        relative_equipment_cost = equipment_cost / demand_size
        relative_rack_cost = rack_count / demand_size
        relative_waste = waste_score / demand_size

        rel_equipment_norm = self._clamp01(
            relative_equipment_cost / self.MAX_REL_EQUIPMENT_COST
        )
        rel_rack_norm = self._clamp01(
            relative_rack_cost / self.MAX_REL_RACK_COST
        )
        rel_waste_norm = self._clamp01(
            relative_waste / self.MAX_REL_WASTE
        )

        base_cost_norm = (
            self.equipment_cost_weight * rel_equipment_norm +
            self.rack_cost_weight * rel_rack_norm +
            self.waste_cost_weight * rel_waste_norm +
            self.logical_cost_weight * logical_norm
        )

        weight_sum = (
            self.equipment_cost_weight +
            self.rack_cost_weight +
            self.waste_cost_weight +
            self.logical_cost_weight
        )

        if weight_sum == 0:
            base_cost_norm = 0.0
        else:
            base_cost_norm = base_cost_norm / weight_sum

        benefit_score = self.compute_benefit_score(
            scalability_norm=scalability_norm,
            redundancy_norm=redundancy_norm,
        )

    
        fair_cost_norm = base_cost_norm * (1.0 - 0.4 * benefit_score)

        return self._clamp01(fair_cost_norm)

    def compute_resource_penalty_norm(
        self,
        demand: DemandVector,
        equipment_cost: float,
        rack_count: int,
        waste_score: float,
    ) -> float:
      
        demand_size = max(float(demand.total_items()), 1.0)

        relative_waste = waste_score / demand_size
        relative_racks = rack_count / demand_size
        relative_equipment_cost = equipment_cost / demand_size

        waste_norm = self._clamp01(relative_waste / self.MAX_REL_WASTE)
        rack_norm = self._clamp01(relative_racks / self.MAX_REL_RACK_COST)
        equipment_norm = self._clamp01(
            relative_equipment_cost / self.MAX_REL_EQUIPMENT_COST
        )

        total_capacity = max(rack_count * self.RACK_CAPACITY, 1.0)
        utilization = self._clamp01(demand_size / total_capacity)
        utilization_penalty = 1.0 - utilization

        resource_penalty_norm = (
            0.35 * waste_norm +
            0.25 * rack_norm +
            0.20 * equipment_norm +
            0.20 * utilization_penalty
        )

        return self._clamp01(resource_penalty_norm)

    def evaluate(
        self,
        topology_key: str,
        topology_name: str,
        demand: DemandVector,
        preferences: UserPreferences,
        topology_metrics: dict[str, float],
        unit_costs: dict[str, float],
        rack_count: int,
        waste_score: float,
    ) -> TopologyEvaluation:
        ws, wr, wc = preferences.normalized_importance()

        scalability_raw = topology_metrics.get("scalability", 0.0)
        redundancy_raw = topology_metrics.get("redundancy", 0.0)
        logical_cost_raw = topology_metrics.get("logical_cost", 0.0)

        scalability_norm = self._clamp01(scalability_raw / self.MAX_SCORE_10)
        redundancy_norm = self._clamp01(redundancy_raw / self.MAX_SCORE_10)

        equipment_cost = self.compute_equipment_cost(
            demand=demand,
            unit_costs=unit_costs,
        )

        fair_cost_norm = self.compute_fair_cost_norm(
            logical_cost_score=logical_cost_raw,
            equipment_cost=equipment_cost,
            rack_count=rack_count,
            waste_score=waste_score,
            demand=demand,
            scalability_norm=scalability_norm,
            redundancy_norm=redundancy_norm,
        )

        resource_penalty_norm = self.compute_resource_penalty_norm(
            demand=demand,
            equipment_cost=equipment_cost,
            rack_count=rack_count,
            waste_score=waste_score,
        )

        total_weight = ws + wr + wc + self.resource_penalty_weight

        if total_weight == 0:
            ws_n = 1.0 / 3.0
            wr_n = 1.0 / 3.0
            wc_n = 1.0 / 3.0
            we_n = 0.0
        else:
            ws_n = ws / total_weight
            wr_n = wr / total_weight
            wc_n = wc / total_weight
            we_n = self.resource_penalty_weight / total_weight

        distance = math.sqrt(
            ws_n * (1.0 - scalability_norm) ** 2 +
            wr_n * (1.0 - redundancy_norm) ** 2 +
            wc_n * (fair_cost_norm - 0.0) ** 2 +
            we_n * (resource_penalty_norm - 0.0) ** 2
        )

        final_score = self._clamp01(1.0 - distance)

        return TopologyEvaluation(
            topology_key=topology_key,
            topology_name=topology_name,
            demand=demand,
            scalability_score=scalability_norm,
            redundancy_score=redundancy_norm,
            logical_cost_score=self._clamp01(logical_cost_raw / self.MAX_SCORE_10),
            equipment_cost=equipment_cost,
            rack_count=rack_count,
            waste_score=waste_score,
            final_score=final_score,
        )