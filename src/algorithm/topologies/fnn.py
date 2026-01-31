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

        pcs_per_zone = int(params.get("pcs_per_zone", 20))
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

    def build_gns3(
        self,
        items: List[Item],
        *,
        normalized: Dict[str, int] | None = None,
        hosts_per_switch: int = 2,
        pcs_per_zone: int = 20,
        zones_per_gateway: int = 3,
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
                "zone": "cloud",
            }

        if normalized is not None:
            generated: List[Item] = []

            for i in range(int(normalized.get("core_routers", 0) or 0)):
                generated.append(Item(id=f"core_router_{i+1}", item_type="core_router"))

            for i in range(int(normalized.get("gateways", 0) or 0)):
                generated.append(Item(id=f"gateway_{i+1}", item_type="agg_switch"))

            for i in range(int(normalized.get("zone_switches", 0) or 0)):
                generated.append(Item(id=f"zone_switch_{i+1}", item_type="edge_switch"))

            for i in range(int(normalized.get("pcs", 0) or 0)):
                generated.append(Item(id=f"pc_{i+1}", item_type="pc"))

            for i in range(int(normalized.get("zones", 0) or 0)):
                generated.append(Item(id=f"zone_{i+1}", item_type="zone"))

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
        zoneSwitches = sortIds("zone_switch_")
        gateways = sortIds("gateway_")
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

        if zoneSwitches:
            for i, pcId in enumerate(pcs):
                zoneSwitchId = zoneSwitches[min(i // max(1, hosts_per_switch), len(zoneSwitches) - 1)]
                addLink(pcId, zoneSwitchId)

        if gateways and zoneSwitches:
            zonesCount = max(1, ceil(len(pcs) / max(1, pcs_per_zone)))
            for zoneIndex in range(zonesCount):
                zoneStart = zoneIndex * max(1, pcs_per_zone)
                zoneEnd = min((zoneIndex + 1) * max(1, pcs_per_zone), len(pcs))
                zoneSwitchStart = zoneStart // max(1, hosts_per_switch)
                zoneSwitchEnd = ceil(zoneEnd / max(1, hosts_per_switch))

                zoneSwitchGroup = zoneSwitches[zoneSwitchStart:zoneSwitchEnd] or zoneSwitches[:1]
                gatewayId = gateways[min(zoneIndex // max(1, zones_per_gateway), len(gateways) - 1)]

                for zoneSwitchId in zoneSwitchGroup:
                    addLink(zoneSwitchId, gatewayId)

        if coreRouters and gateways:
            coreId = coreRouters[0]
            for gatewayId in gateways:
                addLink(gatewayId, coreId)

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
