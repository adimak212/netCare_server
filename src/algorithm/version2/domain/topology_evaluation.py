from __future__ import annotations
from dataclasses import dataclass
from .demand_vector import DemandVector


@dataclass(slots=True)
class TopologyEvaluation:
    topology_key: str
    demand: DemandVector
    topology_name: str
    scalability_score: float
    redundancy_score: float
    logical_cost_score: float
    equipment_cost: float
    rack_count: int
    waste_score: float
    final_score: float

    def as_dict(self) -> dict:
        return {
            "topology": self.topology_key,
            "demand": self.demand.as_dict(),
            "scalability_score": self.scalability_score,
            "redundancy_score": self.redundancy_score,
            "logical_cost_score": self.logical_cost_score,
            "equipment_cost": self.equipment_cost,
            "rack_count": self.rack_count,
            "waste_score": self.waste_score,
            "final_score": self.final_score,
        }