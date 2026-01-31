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

    def build_gns3(
        self,
        items: List[Item],
        *,
        normalized: Dict[str, int] | None = None,
        hosts_per_switch: int = 4,
        switches_per_controller: int = 50,
        template_id_by_type: Dict[str, str] | None = None,
        node_type_by_type: Dict[str, str] | None = None,
        controller_links_to_core: bool = False,
        edge_links_to_core: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if template_id_by_type is None:
            template_id_by_type = {}
        if node_type_by_type is None:
            node_type_by_type = {
                "pc": "vpcs",
                "edge_switch": "ethernet_switch",
                "agg_switch": "ethernet_switch",
                "core_router": "dynamips",
                "sdn_controller": "dynamips",
                "cloud": "cloud",
            }

        if normalized is not None:
            generated: List[Item] = []

            core_count = int(normalized.get("core_routers", 1) or 1)
            for i in range(core_count):
                generated.append(Item(id=f"core_router_{i+1}", item_type="core_router"))

            for i in range(int(normalized.get("controllers", 0) or 0)):
                generated.append(Item(id=f"sdn_controller_{i+1}", item_type="sdn_controller"))

            for i in range(int(normalized.get("edge_switches", 0) or 0)):
                generated.append(Item(id=f"sdn_edge_{i+1}", item_type="edge_switch"))

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
        edgeSwitches = sortIdsByPrefixes(("sdn_edge_", "edge_switch_"))
        controllers = sortIdsByPrefixes(("sdn_controller_",))
        coreRouters = sortIdsByPrefixes(("core_router_",))

        if not coreRouters:
            coreRouters = ["core_router_1"]
            itemsById["core_router_1"] = Item(id="core_router_1", item_type="core_router")

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

        coreId = coreRouters[0]
        if edge_links_to_core:
            for edgeId in edgeSwitches:
                addLink(edgeId, coreId)

        if not controllers:
            controllerCount = max(1, ceil(len(edgeSwitches) / max(1, switches_per_controller)))
            controllers = [f"sdn_controller_{i+1}" for i in range(controllerCount)]
            for controllerId in controllers:
                itemsById[controllerId] = Item(id=controllerId, item_type="sdn_controller")

        for i, edgeId in enumerate(edgeSwitches):
            controllerId = controllers[min(i // max(1, switches_per_controller), len(controllers) - 1)]
            addLink(controllerId, edgeId)

        if controller_links_to_core:
            for controllerId in controllers:
                addLink(controllerId, coreId)

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

        existingNodeIds = {n["node_id"] for n in nodes}
        for nodeId, it in itemsById.items():
            if nodeId not in existingNodeIds:
                nodes.append({
                    "node_id": nodeId,
                    "modelType": it.item_type,
                    "name": nodeId,
                    "node_type": node_type_by_type.get(it.item_type, "dynamips"),
                    "template_id": template_id_by_type.get(it.item_type),
                    "ports": buildPorts(nodeId),
                })

        return nodes, links
