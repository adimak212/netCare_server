from math import ceil
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from ..models import Item, Dims


class FatTree:
    key = "fat_tree"
    name = "Fat Tree"
    Scalability = 0.95
    Redundancy = 0.90
    Cost = 0.70
    
    
    def normalize(self, params) -> Dict[str, int]:
        ROUTER_PORTS_COUNT = 3 
        pcs = int(params.get("pcs", 0))
        hps = int(params.get("hosts_per_switch", 2))
        edge = max(1, ceil(pcs / hps))
        pods = max(1, ceil(edge / 2))
        agg = pods * 2
        core = max(1, ceil(agg / ROUTER_PORTS_COUNT))

        return {"pcs": pcs, "edge_switches": edge, "agg_switches": agg, "core_routers": core, "pods": pods}

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

    