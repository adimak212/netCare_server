from math import ceil
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from ..models import Item, Dims


class Hybrid:
    key = "hybrid"
    name = "Hybrid"
    Scalability = 0.8
    Redundancy = 0.75
    Cost = 0.45

    def normalize(self, params) -> Dict[str, int]:
        pcs = int(params.get("pcs", 0))
        hps = int(params.get("hosts_per_switch", 4))

        edge = max(1, ceil(pcs / hps))
        agg = max(1, ceil(edge / 3))
        core = max(1, ceil(agg / 3))

        return {"pcs": pcs, "edge_switches": edge, "agg_switches": agg, "core_routers": core}

    def build_items(self, n: Dict[str, int], t: Dict[str, Dims]) -> List[Item]:
        items: List[Item] = []

        for i in range(n["core_routers"]):
            items.append(Item(f"core_router_{i+1}", "core_router", "core", t["core_router"], ("core_rack",)))

        for i in range(n["agg_switches"]):
            items.append(Item(f"hybrid_agg_{i+1}", "agg_switch", "aggregation", t["agg_switch"], ("zone_rack",)))

        for i in range(n["edge_switches"]):
            items.append(Item(f"hybrid_edge_{i+1}", "edge_switch", "edge", t["edge_switch"], ("zone_rack",)))

        for i in range(n["pcs"]):
            items.append(Item(f"pc_{i+1}", "pc", "host", t["pc"], ("zone_rack",)))

        return items

    def build_gns3(
        self,
        items: List[Item],
        *,
        normalized: Dict[str, int] | None = None,
        hosts_per_switch: int = 4,
        template_id_by_type: Dict[str, str] | None = None,
        node_type_by_type: Dict[str, str] | None = None,
        extra_agg_mesh: bool = True,
        extra_core_mesh: bool = False,
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
            }

        if normalized is not None:
            generated: List[Item] = []

            for i in range(int(normalized.get("core_routers", 0) or 0)):
                generated.append(Item(id=f"core_router_{i+1}", item_type="core_router"))

            for i in range(int(normalized.get("agg_switches", 0) or 0)):
                generated.append(Item(id=f"hybrid_agg_{i+1}", item_type="agg_switch"))

            for i in range(int(normalized.get("edge_switches", 0) or 0)):
                generated.append(Item(id=f"hybrid_edge_{i+1}", item_type="edge_switch"))

            for i in range(int(normalized.get("pcs", 0) or 0)):
                generated.append(Item(id=f"pc_{i+1}", item_type="pc"))

            items = generated

        itemsById: Dict[str, Item] = {it.id: it for it in items}

        def sortIdsByPrefixes(prefixes: Tuple[str, ...]) -> List[str]:
            def keyFn(x: str):
                for p in prefixes:
                    if x.startswith(p):
                        tail = x[len(p):]
                        try:
                            return (0, int(tail))
                        except ValueError:
                            return (0, tail)
                return (1, x)

            candidates: List[str] = []
            for nodeId in itemsById.keys():
                if any(nodeId.startswith(p) for p in prefixes):
                    candidates.append(nodeId)
            return sorted(candidates, key=keyFn)

        pcs = sortIdsByPrefixes(("pc_",))
        edgeSwitches = sortIdsByPrefixes(("hybrid_edge_", "edge_switch_"))
        aggSwitches = sortIdsByPrefixes(("hybrid_agg_", "agg_switch_"))
        coreRouters = sortIdsByPrefixes(("core_router_",))

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

        def fullMesh(nodeIds: List[str]):
            for i in range(len(nodeIds)):
                for j in range(i + 1, len(nodeIds)):
                    addLink(nodeIds[i], nodeIds[j])

        if edgeSwitches:
            for i, pcId in enumerate(pcs):
                edgeId = edgeSwitches[min(i // max(1, hosts_per_switch), len(edgeSwitches) - 1)]
                addLink(pcId, edgeId)

        if aggSwitches and edgeSwitches:
            for i, edgeId in enumerate(edgeSwitches):
                aggId = aggSwitches[min(i // 3, len(aggSwitches) - 1)]
                addLink(edgeId, aggId)

        if coreRouters and aggSwitches:
            for i, aggId in enumerate(aggSwitches):
                coreId = coreRouters[min(i // 3, len(coreRouters) - 1)]
                addLink(aggId, coreId)

        if extra_agg_mesh and len(aggSwitches) > 1:
            fullMesh(aggSwitches)

        if extra_core_mesh and len(coreRouters) > 1:
            fullMesh(coreRouters)

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
