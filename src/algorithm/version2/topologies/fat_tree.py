from __future__ import annotations
from math import ceil
from typing import Dict, List, Any
from ..models.models import Item , Dims
from .base import TopologyBase
from src.algorithm.version2.domain.demand_vector import DemandVector

ROUTER_PORTS_COUNT = 3 
class FatTreeTopology(TopologyBase):
    key = "fat_tree"
    name = "Fat Tree"
    Scalability = 9.5
    Redundancy = 9.0
    Cost = 7.0
    pcs_per_group = 4
    edge_switches_per_group = 2
    agg_switches_per_group = 2
    switches_per_router = 2

    def normalize(self, params: Dict[str, Any]) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        groups = max(1, ceil(pcs / self.pcs_per_group))
        edge_switches = groups * self.edge_switches_per_group
        agg_switches = groups * self.agg_switches_per_group
        total_switches = edge_switches + agg_switches
        core_routers = max(1, ceil(agg_switches / ROUTER_PORTS_COUNT))
        pods = groups   

        return {
            "pcs": pcs,
            "edge_switches": edge_switches,
            "agg_switches": agg_switches,
            "core_routers": core_routers,
            "pods": pods,
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
            items.append(Item(
                id=f"core_router_{i+1}",
                item_type="core_router",
                layer="core",
                size=t["core_router"],
                allowed_bin_types=("core_rack",),
            ))

        for i in range(n["agg_switches"]):
            items.append(Item(
                id=f"agg_switch_{i+1}",
                item_type="agg_switch",
                layer="aggregation",
                size=t["agg_switch"],
                allowed_bin_types=("zone_rack",)
            ))

        for i in range(n["edge_switches"]):
            items.append(Item(
                id=f"edge_switch_{i+1}",
                item_type="edge_switch",
                layer="edge",
                size=t["edge_switch"],
                allowed_bin_types=("zone_rack",)
            ))

        for i in range(n["pcs"]):
            items.append(Item(
                id=f"pc_{i+1}",
                item_type="pc",
                layer="host",
                size=t["pc"],
                allowed_bin_types=("zone_rack",)
            ))

        return items

    