from __future__ import annotations
from math import ceil
from typing import Any, Dict, List

from .base import TopologyBase
from ..models.models import Item, Dims
from src.algorithm.version2.domain.demand_vector import DemandVector

class MeshTopology(TopologyBase):
    key = "mesh"
    name = "Mesh"

    # 0..10 scale
    Scalability = 85
    Redundancy = 95
    Cost = 80

    switches_per_router = 2

    def normalize(self, params: Dict[str, Any]) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        hps = int(params.get("hosts_per_switch", 4))

        edge = max(1, ceil(pcs / hps))

        # Mesh is switch-based and requires a relatively large backbone layer
        agg = max(1, ceil(edge * 0.8))

        switch_layer_total = edge + agg
        core = max(1, ceil(switch_layer_total / self.switches_per_router))

        return {
            "pcs": pcs,
            "edge_switches": edge,
            "agg_switches": agg,
            "core_routers": core,
        }

    def to_pattern_demand(self, n) -> DemandVector:
        return DemandVector(
            pc=n["pcs"],
            switch=n["edge_switches"] + n["agg_switches"],
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

        for i in range(n["agg_switches"]):
            items.append(
                Item(
                    id=f"mesh_backbone_{i+1}",
                    item_type="agg_switch",
                    layer="backbone",
                    size=t["agg_switch"],
                    allowed_bin_types=("zone_rack",),
                )
            )

        for i in range(n["edge_switches"]):
            items.append(
                Item(
                    id=f"mesh_access_{i+1}",
                    item_type="edge_switch",
                    layer="access",
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