from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class UserPreferences:
    pcs: int
    scalability: float  
    redundancy: float    
    cost: float         

    def normalized_importance(
    self,
    ) -> tuple[float, float, float]:

        scalability = max(
            0.0,
            min(100.0, self.scalability)
        )

        redundancy = max(
            0.0,
            min(100.0, self.redundancy)
        )

        cost = max(
            0.0,
            min(100.0, self.cost)
        )

        total = (
            scalability +
            redundancy +
            cost
        )

        if total == 0:
            return (
                1 / 3,
                1 / 3,
                1 / 3,
            )

        return (
            scalability / total,
            redundancy / total,
            cost / total,
        )