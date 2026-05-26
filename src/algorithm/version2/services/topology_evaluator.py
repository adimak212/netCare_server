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
        self.benefit_lambda = 0.4
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

    
        benefit_factor = (
            1.0 +
            self.benefit_lambda *
            benefit_score
        )

        fair_cost_norm = (
            base_cost_norm /
            benefit_factor
        )

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
        topology_key:str,
        topology_name:str,
        demand:DemandVector,
        preferences:UserPreferences,
        topology_metrics:dict[str,float],
        unit_costs:dict[str,float],
        rack_count:int,
        waste_score:float,
    )->TopologyEvaluation:

        ws,wr,wc=preferences.normalized_importance()

        scalability_norm=self._clamp01(
            topology_metrics.get("scalability",0.0)/
            self.MAX_SCORE_10
        )

        redundancy_norm=self._clamp01(
            topology_metrics.get("redundancy",0.0)/
            self.MAX_SCORE_10
        )

        logical_cost_raw=topology_metrics.get(
            "logical_cost",
            0.0,
        )

        connectivity_score=topology_metrics.get(
            "connectivity_score",
            0.0,
        )

        resilience_score=topology_metrics.get(
            "resilience_score",
            0.20,
        )

        degree_balance_score=topology_metrics.get(
            "degree_balance_score",
            0.0,
        )

        diameter_score=topology_metrics.get(
            "diameter_score",
            0.0,
        )

        centralization_penalty=topology_metrics.get(
            "centralization_penalty",
            0.0,
        )

        edge_count=topology_metrics.get(
            "edge_count",
            0.0,
        )

        node_count=max(
            topology_metrics.get(
                "node_count",
                demand.pc,
            ),
            1,
        )

        edge_density=self._clamp01(
            (2*edge_count)/
            max(node_count*(node_count-1),1)
        )

        density_penalty=edge_density**2

        link_cost=edge_count*35

        equipment_cost=(
            self.compute_equipment_cost(
                demand=demand,
                unit_costs=unit_costs,
            )+
            link_cost
        )

        fair_cost_norm=(
            self.compute_fair_cost_norm(
                logical_cost_score=logical_cost_raw,
                equipment_cost=equipment_cost,
                rack_count=rack_count,
                waste_score=waste_score,
                demand=demand,
                scalability_norm=scalability_norm,
                redundancy_norm=redundancy_norm,
            )
        )

        resource_penalty_norm=(
            self.compute_resource_penalty_norm(
                demand=demand,
                equipment_cost=equipment_cost,
                rack_count=rack_count,
                waste_score=waste_score,
            )
        )

        graph_score=self._clamp01(
            connectivity_score*0.20+
            resilience_score*0.20+
            degree_balance_score*0.15+
            diameter_score*0.15+
            (1-centralization_penalty)*0.20+
            (1-density_penalty)*0.10
        )

        resource_score=self._clamp01(
            (1-fair_cost_norm)*0.45+
            (1-resource_penalty_norm)*0.45+
            (1-density_penalty)*0.10
        )

        scalability_target=ws/100
        redundancy_target=wr/100
        cost_target=wc/100

        scalability_match=1.0-abs(
            scalability_norm-
            scalability_target
        )

        redundancy_match=1.0-abs(
            redundancy_norm-
            redundancy_target
        )

        cost_match=1.0-abs(
            (1-fair_cost_norm)-
            cost_target
        )

        user_preference_score=self._clamp01(
            scalability_match*0.40+
            redundancy_match*0.40+
            cost_match*0.20
        )

        architecture_fit=0.0

        if demand.pc>=15:
            if topology_key=="fat_tree":
                architecture_fit+=0.05
            if topology_key=="mesh":
                architecture_fit-=0.05

        if demand.pc<=10:
            if topology_key=="mesh":
                architecture_fit+=0.08
            if topology_key=="sdn":
                architecture_fit+=0.05

        if wc>=70:
            if topology_key=="fnn":
                architecture_fit+=0.08
            if topology_key=="mesh":
                architecture_fit-=0.05

        if ws>=70:
            if topology_key=="fat_tree":
                architecture_fit+=0.08
            if topology_key=="sdn":
                architecture_fit+=0.05

        if wr>=70:
            if topology_key=="mesh":
                architecture_fit+=0.05

        final_score=self._clamp01(
            graph_score*0.30+
            resource_score*0.50+
            user_preference_score*0.20+
            architecture_fit
        )

        return TopologyEvaluation(
            topology_key=topology_key,
            topology_name=topology_name,
            demand=demand,
            scalability_score=scalability_norm,
            redundancy_score=redundancy_norm,
            logical_cost_score=self._clamp01(
                logical_cost_raw/self.MAX_SCORE_10
            ),
            equipment_cost=equipment_cost,
            rack_count=rack_count,
            waste_score=waste_score,
            final_score=final_score,
        )