from __future__ import annotations
from math import ceil
from typing import Any, Dict, List
from .base import TopologyBase
from ..models.models import Item, Dims
from src.algorithm.version2.domain.demand_vector import DemandVector

class SDNTopology(TopologyBase):
    key = "sdn"
    name = "Software Defined Network"
    Scalability = 90
    Redundancy = 70
    Cost = 40

    switches_per_router = 3

    def normalize(self, params: Dict[str, Any]) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        hps = int(params.get("hosts_per_switch", 4))
        spc = int(params.get("switches_per_controller", 50))

        edge = max(1, ceil(pcs / hps))
        controllers = max(1, ceil(edge / spc))
        core_routers = max(1, ceil(edge / self.switches_per_router))

        return {
            "pcs": pcs,
            "edge_switches": edge,
            "controllers": controllers,
            "core_routers": core_routers,
        }
    
    def to_pattern_demand(self, n) -> DemandVector:
        return DemandVector(
            pc=n["pcs"],
            switch=n["edge_switches"],
            router=n["core_routers"],
            controller=n["controllers"]
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

        for i in range(n["controllers"]):
            items.append(
                Item(
                    id=f"sdn_controller_{i+1}",
                    item_type="sdn_controller",
                    layer="control",
                    size=t["sdn_controller"],
                    allowed_bin_types=("ctrl_rack",),
                )
            )

        for i in range(n["edge_switches"]):
            items.append(
                Item(
                    id=f"sdn_edge_{i+1}",
                    item_type="edge_switch",
                    layer="data",
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