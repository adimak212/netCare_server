from math import ceil
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from ..models import Item, Dims


class SDN:
    key = "sdn"
    name = "Software Defined Network"
    Scalability = 0.9
    Redundancy = 0.7
    Cost = 0.4

    def normalize(self, params) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        hps = int(params.get("hosts_per_switch", 4))
        spc = int(params.get("switches_per_controller", 50))

        edge = max(1, ceil(pcs / hps))
        controllers = max(1, ceil(edge / spc))

        return {
            "pcs": pcs,
            "edge_switches": edge,
            "controllers": controllers,
            "core_routers": 1
        }

    def build_items(self, n: Dict[str, int], t: Dict[str, Dims]) -> List[Item]:
        items: List[Item] = []

        items.append(Item("core_router_1", "core_router", "core", t["core_router"], ("core_rack",)))

        for i in range(n["controllers"]):
            items.append(Item(
                id=f"sdn_controller_{i+1}",
                item_type="sdn_controller",
                layer="control",
                size=t["sdn_controller"],
                allowed_bin_types=("ctrl_rack",)
            ))

        for i in range(n["edge_switches"]):
            items.append(Item(f"sdn_edge_{i+1}", "edge_switch", "data", t["edge_switch"], ("zone_rack",)))

        for i in range(n["pcs"]):
            items.append(Item(f"pc_{i+1}", "pc", "host", t["pc"], ("zone_rack",)))

        return items

    