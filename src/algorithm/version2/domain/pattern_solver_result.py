from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.domain.resources import Resources


@dataclass
class PatternSolveResult:
    rack_count: int
    waste_score: float
    remaining: DemandVector
    pattern_usage: list[dict[str, Any]] = field(default_factory=list)

    provided: DemandVector = field(
        default_factory=lambda: DemandVector(pc=0, switch=0, router=0, controller=0)
    )
    used_resources: Resources = field(default_factory=Resources)
    total_capacity: Resources = field(default_factory=Resources)
    waste_breakdown: dict[str, Any] = field(default_factory=dict)

    def is_fully_satisfied(self) -> bool:
        return self.remaining.is_zero()

    def as_dict(self) -> dict:
        return {
            "rack_count": self.rack_count,
            "waste_score": self.waste_score,
            "remaining": self.remaining.as_dict(),
            "pattern_usage": self.pattern_usage,
            "provided": self.provided.as_dict(),
            "used_resources": {
                "u": self.used_resources.u,
                "watt": self.used_resources.watt,
                "cost": self.used_resources.cost,
                "ports": self.used_resources.ports,
            },
            "total_capacity": {
                "u": self.total_capacity.u,
                "watt": self.total_capacity.watt,
                "cost": self.total_capacity.cost,
                "ports": self.total_capacity.ports,
            },
            "waste_breakdown": self.waste_breakdown,
            "fully_satisfied": self.is_fully_satisfied(),
        }