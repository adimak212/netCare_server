from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class UserPreferences:
    pcs: int
    scalability: float  
    redundancy: float    
    cost: float         

    def normalized_importance(self) -> tuple[float, float, float]:
      return (
            max(0.0, min(100.0, self.scalability)) / 100.0,
            max(0.0, min(100.0, self.redundancy)) / 100.0,
            max(0.0, min(100.0, self.cost)) / 100.0,
        )