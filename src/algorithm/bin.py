from dataclasses import dataclass
from typing import List

@dataclass
class Bin:
    id: str
    type: str
    capacity: float
    layer: str
    used: float = 0
    components: List[dict] = None

    def __post_init__(self):
        if self.components is None:
            self.components = []

    def can_fit(self, weight: float) -> bool:
        return self.used + weight <= self.capacity

    def add(self, item: dict):
        self.components.append(item)
        self.used += item["weight"]
