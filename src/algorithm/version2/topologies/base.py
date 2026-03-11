from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class TopologyBase(ABC):
    key: str = "base"
    name: str = "Base Topology"
    Scalability: float = 0.0
    Redundancy: float = 0.0
    Cost: float = 0.0

    @abstractmethod
    def normalize(self, params: Dict[str, Any]) -> Dict[str, int]:
        pass

    @abstractmethod
    def build_items(self, n: Dict[str, int], t: Dict[str, Any]) -> List[Any]:
        pass

    def metrics(self) -> dict[str, float]:
        return {
            "scalability": self.Scalability,
            "redundancy": self.Redundancy,
            "logical_cost": self.Cost,
        }