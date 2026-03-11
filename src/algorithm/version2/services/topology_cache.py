from __future__ import annotations
from typing import Dict, Tuple, Any


class TopologyCache:
    """
    Cache for topology normalization + pattern solving results.
    Keyed by (topology_key, pcs)
    """

    def __init__(self):
        self._store: Dict[Tuple[str, int], Dict[str, Any]] = {}

    def get(self, topology_key: str, pcs: int):
        return self._store.get((topology_key, pcs))

    def set(self, topology_key: str, pcs: int, value: Dict[str, Any]):
        self._store[(topology_key, pcs)] = value

    def has(self, topology_key: str, pcs: int) -> bool:
        return (topology_key, pcs) in self._store

    def size(self) -> int:
        return len(self._store)