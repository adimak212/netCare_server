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

