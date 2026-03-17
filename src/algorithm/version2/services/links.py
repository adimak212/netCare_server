from __future__ import annotations
from uuid import uuid4
from typing import Any, Dict, List, Tuple

Node = Dict[str, Any]
Link = Dict[str, Any]


def build_links(
    nodes: List[Node],
    topology: str,
    *,
    hosts_per_switch: int = 4,
    switch_ports: int = 8,
    cloud_ports: int = 8,
) -> List[Link]:

    by_layer: Dict[str, List[str]] = {}
    for n in nodes:
        by_layer.setdefault(n["layer"], []).append(n["name"])

    node_by_name = {n["name"]: n for n in nodes}
    name_to_index = {n["name"]: n["index"] for n in nodes}

    ROUTER_PORTS = [
        (0, 0, "FastEthernet0/0"),
        (2, 0, "FastEthernet2/0"),
        (2, 1, "FastEthernet2/1"),
    ]

    port_pool: Dict[str, List[Dict[str, Any]]] = {}
    port_idx: Dict[str, int] = {}
    used_ports: Dict[str, set] = {}

    def init_pool(node_name: str):
        if node_name in port_pool:
            return
        nt = node_by_name[node_name]["node_type"]
        if nt == "vpcs":
            pool = [{"adapter_number": 0, "port_number": 0, "port": "e0"}]
        elif nt == "ethernet_switch":
            pool = [{"adapter_number": 0, "port_number": i, "port": f"e{i}"} for i in range(switch_ports)]
        elif nt == "cloud":
            pool = [{"adapter_number": 0, "port_number": i, "port": f"e{i}"} for i in range(cloud_ports)]
        elif nt == "dynamips":
            pool = [{"adapter_number": a, "port_number": p, "port": l} for a, p, l in ROUTER_PORTS]
        else:
            pool = [{"adapter_number": 1, "port_number": i, "port": f"e{i}"} for i in range(switch_ports)]
        port_pool[node_name] = pool
        port_idx[node_name] = 0
        used_ports[node_name] = set()

    def alloc_port(node_name: str) -> Dict[str, Any]:
        init_pool(node_name)
        pool = port_pool[node_name]
        for k in range(len(pool)):
            i = (port_idx[node_name] + k) % len(pool)
            cand = pool[i]
            key = (cand["adapter_number"], cand["port_number"])
            if key not in used_ports[node_name]:
                used_ports[node_name].add(key)
                port_idx[node_name] = (i + 1) % len(pool)
                return {
                    "node_id": node_name,
                    "adapter_number": cand["adapter_number"],
                    "port_number": cand["port_number"],
                    "port": cand["port"],
                    "index": name_to_index[node_name],
                }
        raise RuntimeError(f"No free ports on {node_name}")

    links: List[Link] = []
    seen: set[Tuple[str, str]] = set()

    def add_link(a: str, b: str):
        if a == b:
            return
        key = tuple(sorted((a, b)))
        if key in seen:
            return
        seen.add(key)
        links.append({
            "link_id": str(uuid4()),
            "from": alloc_port(a),
            "to": alloc_port(b),
        })

    pcs = by_layer.get("pcs", [])
    edge = by_layer.get("edge_switches", [])
    agg = by_layer.get("agg_switches", [])
    core = by_layer.get("core_routers", [])
    controllers = by_layer.get("controllers", [])

    topology = topology.lower().strip()
    hps = max(1, int(hosts_per_switch))
    hps_fat_tree = 2;
    if topology == "sdn":
        for i, pc in enumerate(pcs):
            add_link(pc, edge[min(i // hps, len(edge) - 1)])
        for i, esw in enumerate(edge):
            add_link(esw, core[i % len(core)])
        if controllers:
            for i, esw in enumerate(edge):
                add_link(controllers[i % len(controllers)], esw)
        return links

    if topology == "hybrid":
        # PCs -> Edge (Star)
        for i, pc in enumerate(pcs):
            add_link(pc, edge[min(i // hps, len(edge) - 1)])

        core_port_limit = 3
        core_used_ports = {router: 0 for router in core}

        # Core <-> Core (Ring)
        if len(core) == 2:
            add_link(core[0], core[1])
            core_used_ports[core[0]] += 1
            core_used_ports[core[1]] += 1

        elif len(core) > 2:
            for i in range(len(core)):
                a = core[i]
                b = core[(i + 1) % len(core)]
                add_link(a, b)
                core_used_ports[a] += 1
                core_used_ports[b] += 1

        # Edge -> Core
        core_index = 0
        for esw in edge:
            assigned = False
            attempts = 0

            while attempts < len(core):
                router = core[core_index % len(core)]

                if core_used_ports[router] < core_port_limit:
                    add_link(esw, router)
                    core_used_ports[router] += 1
                    assigned = True
                    core_index += 1
                    break

                core_index += 1
                attempts += 1

            if not assigned:
                raise ValueError(
                    "Not enough free router ports in hybrid topology to connect all edge switches"
                )

        return links
    if topology == "fat_tree":
        for i, pc in enumerate(pcs):
            add_link(pc, edge[min(i // hps_fat_tree, len(edge) - 1)])
        for i in range(0, len(edge), 2):
            for k in range(min(2, len(agg))):
                add_link(edge[i], agg[(i + k) % len(agg)])
                if i + 1 < len(edge):
                    add_link(edge[i + 1], agg[(i + k) % len(agg)])
        for i, a in enumerate(agg):
            add_link(a, core[i % len(core)])
        return links

    if topology == "mesh":
        for i, pc in enumerate(pcs):
            add_link(pc, edge[min(i // hps, len(edge) - 1)])
        for i, esw in enumerate(edge):
            add_link(esw, agg[i % len(agg)])
        for i in range(len(agg)):
            for j in range(i + 1, len(agg)):
                add_link(agg[i], agg[j])
        for i, a in enumerate(agg):
            add_link(a, core[i % len(core)])
        return links

    if topology == "fnn":
        zone = by_layer.get("zone_switches", [])
        gateways = by_layer.get("gateways", [])
        for i, pc in enumerate(pcs):
            add_link(pc, zone[min(i // hps, len(zone) - 1)])
        for i, sw in enumerate(zone):
            add_link(sw, gateways[i % len(gateways)])
        for gw in gateways:
            add_link(gw, core[0])
        return links

    return links
