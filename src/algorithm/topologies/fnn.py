from math import ceil
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from ..models import Item, Dims


class FNN:
    key = "fnn"
    name = "Flat Neighborhood Network"

    Scalability = 0.65
    Redundancy = 0.60
    Cost = 0.25

    def normalize(self, params) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        hosts_per_switch = int(params.get("hosts_per_switch", 4))

        pcs_per_zone = int(params.get("pcs_per_zone", 4))
        zones_per_gateway = int(params.get("zones_per_gateway", 3))

        zones = max(1, ceil(pcs / pcs_per_zone))
        zone_switches = max(1, ceil(pcs / hosts_per_switch))
        gateways = max(1, ceil(zones / zones_per_gateway))
        core_routers = 1

        return {
            "pcs": pcs,
            "zones": zones,
            "zone_switches": zone_switches,
            "gateways": gateways,
            "core_routers": core_routers
        }

    def build_items(self, n: Dict[str, int], t: Dict[str, Dims]) -> List[Item]:
        items: List[Item] = []

        for i in range(n.get("core_routers", 0)):
            items.append(Item(
                id=f"core_router_{i+1}",
                item_type="core_router",
                layer="core",
                size=t["core_router"],
                allowed_bin_types=("core_rack",)
            ))

        for i in range(n["gateways"]):
            items.append(Item(
                id=f"gateway_{i+1}",
                item_type="agg_switch",
                layer="gateway",
                size=t["agg_switch"],
                allowed_bin_types=("zone_rack",)
            ))

        for i in range(n["zone_switches"]):
            items.append(Item(
                id=f"zone_switch_{i+1}",
                item_type="edge_switch",
                layer="zone_access",
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
