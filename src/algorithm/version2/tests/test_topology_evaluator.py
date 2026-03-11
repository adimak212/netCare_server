from src.algorithm.version2.domain.user_preferences import UserPreferences
from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.services.topology_evaluator import TopologyEvaluator


def main():
    preferences = UserPreferences(
        pcs=20,
        scalability_weight=5,
        redundancy_weight=3,
        cost_weight=2,
    )

    demand = DemandVector(
        pc=20,
        switch=6,
        router=2,
    )

    topology_metrics = {
        "scalability": 9.0,
        "redundancy": 8.0,
        "logical_cost": 4.0,
    }

    unit_costs = {
        "pc": 200,
        "switch": 1500,
        "router": 5000,
    }

    rack_count = 3
    waste_score = 1.5

    evaluator = TopologyEvaluator(
        rack_cost_weight=1.0,
        waste_cost_weight=1.0,
        equipment_cost_weight=0.001,
    )

    result = evaluator.evaluate(
        topology_key="fat_tree",
        demand=demand,
        preferences=preferences,
        topology_metrics=topology_metrics,
        unit_costs=unit_costs,
        rack_count=rack_count,
        waste_score=waste_score,
    )

    print(result.as_dict())


if __name__ == "__main__":
    main()