import json
import os
from dataclasses import dataclass
from typing import List

@dataclass
class Topology:
    type: str
    name: str
    base_capacity: float
    dynamic_factor: float
    scalability: float
    redundancy: float
    cost: float

    def capacity(self, num_components: int) -> float:
        return self.base_capacity + self.dynamic_factor * num_components


class TopologyManager:
    _topologies: List[Topology] | None = None

    @classmethod
    def init(cls, filepath: str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Topologies file not found: {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        cls._topologies = [Topology(**item) for item in data]

    @classmethod
    def all(cls) -> List[Topology]:
        if cls._topologies is None:
            raise RuntimeError("TopologyManager not initialized.")
        return cls._topologies
