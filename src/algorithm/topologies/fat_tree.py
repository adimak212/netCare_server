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
                allowed_bin_types=("core_rack",)
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

    def build_gns3(
        self,
        items: List[Item],
        *,
        normalized: Dict[str, int] | None = None,
        hosts_per_switch: int = 2,
        template_id_by_type: Dict[str, str] | None = None,
        node_type_by_type: Dict[str, str] | None = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if template_id_by_type is None:
            template_id_by_type = {}
        if node_type_by_type is None:
            node_type_by_type = {
                "pc": "vpcs",
                "edge_switch": "ethernet_switch",
                "agg_switch": "ethernet_switch",
                "core_router": "dynamips",
                "controller": "dynamips",
                "cloud": "cloud",
                "pod": "cloud",
            }

        if normalized is not None:
            generated: List[Item] = []

            for i in range(int(normalized.get("core_routers", 0) or 0)):
                generated.append(Item(id=f"core_router_{i+1}", item_type="core_router"))

            for i in range(int(normalized.get("agg_switches", 0) or 0)):
                generated.append(Item(id=f"agg_switch_{i+1}", item_type="agg_switch"))

            for i in range(int(normalized.get("edge_switches", 0) or 0)):
                generated.append(Item(id=f"edge_switch_{i+1}", item_type="edge_switch"))

            for i in range(int(normalized.get("pcs", 0) or 0)):
                generated.append(Item(id=f"pc_{i+1}", item_type="pc"))

            for i in range(int(normalized.get("pods", 0) or 0)):
                generated.append(Item(id=f"pod_{i+1}", item_type="pod"))

            items = generated

        itemsById: Dict[str, Item] = {it.id: it for it in items}

        def sortIds(prefix: str) -> List[str]:
            def keyFn(x: str):
                if not x.startswith(prefix):
                    return (1, x)
                tail = x[len(prefix):]
                try:
                    return (0, int(tail))
                except ValueError:
                    return (0, tail)
            return sorted([i for i in itemsById.keys() if i.startswith(prefix)], key=keyFn)

        pcs = sortIds("pc_")
        edgeSwitches = sortIds("edge_switch_")
        aggSwitches = sortIds("agg_switch_")
        coreRouters = sortIds("core_router_")

        portCounter: Dict[str, int] = {}

        def allocPort(nodeId: str) -> Dict[str, int]:
            portNumber = portCounter.get(nodeId, 0)
            portCounter[nodeId] = portNumber + 1
            return {"adapter_number": 0, "port_number": portNumber}

        links: List[Dict[str, Any]] = []

        def addLink(a: str, b: str):
            links.append({
                "link_id": str(uuid4()),
                "from": {"node_id": a, **allocPort(a)},
                "to": {"node_id": b, **allocPort(b)},
            })

        if edgeSwitches:
            for i, pcId in enumerate(pcs):
                edgeId = edgeSwitches[min(i // max(1, hosts_per_switch), len(edgeSwitches) - 1)]
                addLink(pcId, edgeId)

        for edgeId in edgeSwitches:
            for aggId in aggSwitches:
                addLink(edgeId, aggId)

        for aggId in aggSwitches:
            for coreId in coreRouters:
                addLink(aggId, coreId)

        def buildPorts(nodeId: str) -> List[Dict[str, Any]]:
            return [
                {"link_type": "ethernet", "port_number": i, "short_name": f"e{i}", "adapter_number": 0}
                for i in range(portCounter.get(nodeId, 0))
            ]

        nodes: List[Dict[str, Any]] = []
        for it in items:
            nodes.append({
                "node_id": it.id,
                "modelType": it.item_type,
                "name": it.id,
                "node_type": node_type_by_type.get(it.item_type, "dynamips"),
                "template_id": template_id_by_type.get(it.item_type),
                "ports": buildPorts(it.id),
            })

        return nodes, links
