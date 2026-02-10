from math import ceil
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from ..models import Item, Dims


class Mesh:
    key = "mesh"
    name = "Mesh"
    Scalability = 0.85
    Redundancy = 0.95
    Cost = 0.8

    def normalize(self, params) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        hps = int(params.get("hosts_per_switch", 4))

        edge = max(1, ceil(pcs / hps))
        agg = max(1, ceil(edge * 0.8))
        core = max(1, ceil(agg / 3))

        return {
            "pcs": pcs,
            "edge_switches": edge,
            "agg_switches": agg,
            "core_routers": core,
        }

    def build_items(self, n: Dict[str, int], t: Dict[str, Dims]) -> List[Item]:
        items: List[Item] = []

        for i in range(n["core_routers"]):
            items.append(Item(f"core_router_{i+1}", "core_router", "core", t["core_router"], ("core_rack",)))

        for i in range(n["agg_switches"]):
            items.append(Item(f"mesh_backbone_{i+1}", "agg_switch", "backbone", t["agg_switch"], ("zone_rack",)))

        for i in range(n["edge_switches"]):
            items.append(Item(f"mesh_access_{i+1}", "edge_switch", "access", t["edge_switch"], ("zone_rack",)))

        for i in range(n["pcs"]):
            items.append(Item(f"pc_{i+1}", "pc", "host", t["pc"], ("zone_rack",)))

        return items

    

    