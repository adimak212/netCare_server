from __future__ import annotations
from math import ceil
from typing import Any, Dict, List
from .base import TopologyBase
from ..models.models import Item, Dims
from src.algorithm.version2.domain.demand_vector import DemandVector

class HybridTopology(TopologyBase):
    key = "hybrid"
    name = "Hybrid"

    # 0..10 scale
    Scalability = 80
    Redundancy = 75
    Cost = 45

    switches_per_router = 3

    def normalize(self, params: Dict[str, Any]) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        hosts_per_switch = int(params.get("hosts_per_switch", 4))

        edge = max(1, ceil(pcs / hosts_per_switch))

        # התאמה למודל Star + Mesh עם 3 פורטים ל-router
        if edge <= 4:
            core = 2
        else:
            core = edge

        return {
            "pcs": pcs,
            "edge_switches": edge,
            "core_routers": core,
        }
            
    def to_pattern_demand(self, n) -> DemandVector:
        return DemandVector(
            pc=n["pcs"],
            switch=n["edge_switches"],
            router=n["core_routers"],
            controller=0
        )

    def build_items(self, n: Dict[str, int], t: Dict[str, Dims]) -> List[Item]:
        items: List[Item] = []

        for i in range(n["core_routers"]):
            items.append(
                Item(
                    id=f"core_router_{i+1}",
                    item_type="core_router",
                    layer="core",
                    size=t["core_router"],
                    allowed_bin_types=("core_rack",),
                )
            )

        for i in range(n.get("agg_switches", 0)):
            items.append(
                Item(
                    id=f"hybrid_agg_{i+1}",
                    item_type="agg_switch",
                    layer="aggregation",
                    size=t["agg_switch"],
                    allowed_bin_types=("zone_rack",),
                )
            )

        for i in range(n["edge_switches"]):
            items.append(
                Item(
                    id=f"hybrid_edge_{i+1}",
                    item_type="edge_switch",
                    layer="edge",
                    size=t["edge_switch"],
                    allowed_bin_types=("zone_rack",),
                )
            )

        for i in range(n["pcs"]):
            items.append(
                Item(
                    id=f"pc_{i+1}",
                    item_type="pc",
                    layer="host",
                    size=t["pc"],
                    allowed_bin_types=("zone_rack",),
                )
            )

        return items