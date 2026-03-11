from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

Dims = Dict[str, float] 

def add_dims(a: Dims, b: Dims) -> Dims:
    return {k: a.get(k, 0.0) + b.get(k, 0.0) for k in set(a) | set(b)}

def sub_dims(a: Dims, b: Dims) -> Dims:
    return {k: a.get(k, 0.0) - b.get(k, 0.0) for k in set(a) | set(b)}

def leq_dims(a: Dims, b: Dims) -> bool:
    for k, v in a.items():
        if v > b.get(k, 0.0):
            return False
    return True

@dataclass(frozen=True)
class Item:
    id: str
    item_type: str
    layer: str
    size: Dims
    allowed_bin_types: Tuple[str, ...]

@dataclass
class Bin:
    id: str
    bin_type: str
    capacity: Dims
    used: Dims = field(default_factory=dict)
    items: List[Item] = field(default_factory=list)

    def can_accept(self, item: Item) -> bool:
        if self.bin_type not in item.allowed_bin_types:
            return False
        new_used = add_dims(self.used, item.size)
        return leq_dims(new_used, self.capacity)

    def add(self, item: Item) -> None:
        if not self.can_accept(item):
            raise ValueError(f"Item {item.id} cannot fit in {self.id}")
        self.used = add_dims(self.used, item.size)
        self.items.append(item)

    def remaining(self) -> Dims:
        return sub_dims(self.capacity, self.used)
