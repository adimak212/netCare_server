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
    switch_ports: int = 16,
    cloud_ports: int = 8,
) -> List[Link]:

    layer_aliases = {
        "core": "core_routers",
        "aggregation": "agg_switches",
        "backbone": "agg_switches",
        "gateway": "gateways",

        "edge": "edge_switches",
        "access": "edge_switches",
        "zone_access": "zone_switches",
        "data": "edge_switches",

        "host": "pcs",

        "controller": "controllers",
        "control": "controllers",
    }

    by_layer: Dict[str, List[str]] = {}

    for n in nodes:

        raw_layer = n["layer"]

        canonical = layer_aliases.get(
            raw_layer,
            raw_layer,
        )

        by_layer.setdefault(
            canonical,
            [],
        ).append(
            n["name"]
        )

    node_by_name = {
        n["name"]: n
        for n in nodes
    }

    name_to_index = {
        n["name"]: n["index"]
        for n in nodes
    }

    ROUTER_PORTS = [
        (0, 0, "FastEthernet0/0"),
        (2, 0, "FastEthernet2/0"),
        (2, 1, "FastEthernet2/1"),
    ]

    port_pool: Dict[
        str,
        List[Dict[str, Any]]
    ] = {}

    port_idx: Dict[str, int] = {}

    used_ports: Dict[str, set] = {}

    def safe_get(
        arr: List[str],
        idx: int,
    ) -> str:

        if not arr:
            raise ValueError(
                "Empty topology layer"
            )

        return arr[
            idx % len(arr)
        ]

    def validate_non_empty(
        layer_name: str,
        arr: List[str],
    ):

        if not arr:
            raise ValueError(
                f"Missing layer: {layer_name}"
            )

    def init_pool(
        node_name: str,
    ):

        if node_name in port_pool:
            return

        nt = node_by_name[
            node_name
        ]["node_type"]

        if nt == "vpcs":

            pool = [{
                "adapter_number": 0,
                "port_number": 0,
                "port": "e0",
            }]

        elif nt in (
            "qemu",
            "ethernet_switch",
            "iou",
        ):

            pool = [{
                "adapter_number": i,
                "port_number": 0,
                "port": f"Gi{i // 4}/{i % 4}",
            } for i in range(switch_ports)]

        elif nt == "cloud":

            pool = [{
                "adapter_number": 0,
                "port_number": i,
                "port": f"e{i}",
            } for i in range(cloud_ports)]

        elif nt == "dynamips":

            pool = [{
                "adapter_number": a,
                "port_number": p,
                "port": l,
            } for a, p, l in ROUTER_PORTS]

        else:

            pool = [{
                "adapter_number": 1,
                "port_number": i,
                "port": f"e{i}",
            } for i in range(switch_ports)]

        port_pool[node_name] = pool

        port_idx[node_name] = 0

        used_ports[node_name] = set()

    def alloc_port(
        node_name: str,
    ) -> Dict[str, Any]:

        init_pool(node_name)

        pool = port_pool[node_name]

        for k in range(len(pool)):

            i = (
                port_idx[node_name] + k
            ) % len(pool)

            cand = pool[i]

            key = (
                cand["adapter_number"],
                cand["port_number"],
            )

            if key not in used_ports[node_name]:

                used_ports[node_name].add(
                    key
                )

                port_idx[node_name] = (
                    i + 1
                ) % len(pool)

                return {
                    "node_id": node_name,
                    "adapter_number": cand["adapter_number"],
                    "port_number": cand["port_number"],
                    "port": cand["port"],
                    "index": name_to_index[node_name],
                }

        raise RuntimeError(
            f"No free ports on {node_name}"
        )

    links: List[Link] = []

    seen: set[Tuple[str, str]] = set()

    def add_link(
        a: str,
        b: str,
    ):

        if a == b:
            return

        key = tuple(
            sorted((a, b))
        )

        if key in seen:
            return

        seen.add(key)

        links.append({
            "link_id": str(uuid4()),
            "from": alloc_port(a),
            "to": alloc_port(b),
        })

    pcs = by_layer.get("pcs", [])

    edge = by_layer.get(
        "edge_switches",
        [],
    )

    agg = by_layer.get(
        "agg_switches",
        [],
    )

    zone = by_layer.get(
        "zone_switches",
        [],
    )

    gateways = by_layer.get(
        "gateways",
        [],
    )

    core = by_layer.get(
        "core_routers",
        [],
    )

    controllers = by_layer.get(
        "controllers",
        [],
    )

    topology = topology.lower().strip()

    hps = max(
        1,
        int(hosts_per_switch),
    )

    hps_fat_tree = 2

    if topology == "sdn":

        validate_non_empty(
            "edge_switches",
            edge,
        )

        validate_non_empty(
            "core_routers",
            core,
        )

        for i, pc in enumerate(pcs):

            add_link(
                pc,
                edge[
                    min(
                        i // hps,
                        len(edge) - 1,
                    )
                ],
            )

        for i, esw in enumerate(edge):

            add_link(
                esw,
                safe_get(core, i),
            )

        for i, esw in enumerate(edge):

            if controllers:

                add_link(
                    controllers[
                        i % len(controllers)
                    ],
                    esw,
                )

        return links

    if topology == "hybrid":

        validate_non_empty(
            "edge_switches",
            edge,
        )

        validate_non_empty(
            "core_routers",
            core,
        )

        for i, pc in enumerate(pcs):

            add_link(
                pc,
                edge[
                    min(
                        i // hps,
                        len(edge) - 1,
                    )
                ],
            )

        if len(core) == 2:

            add_link(
                core[0],
                core[1],
            )

        elif len(core) > 2:

            for i in range(len(core)):

                add_link(
                    core[i],
                    core[
                        (i + 1) % len(core)
                    ],
                )

        for i, esw in enumerate(edge):

            add_link(
                esw,
                safe_get(core, i),
            )

        return links

    if topology == "fat_tree":

        validate_non_empty(
            "edge_switches",
            edge,
        )

        validate_non_empty(
            "agg_switches",
            agg,
        )

        validate_non_empty(
            "core_routers",
            core,
        )

        for i, pc in enumerate(pcs):

            edge_index = min(
                i // hps_fat_tree,
                len(edge) - 1,
            )

            add_link(
                pc,
                edge[edge_index],
            )

        pod_size = 2

        if len(edge) % pod_size != 0:

            raise ValueError(
                "FatTree requires even edge switches"
            )

        for pod_start in range(
            0,
            len(edge),
            pod_size,
        ):

            pod_edges = edge[
                pod_start:
                pod_start + pod_size
            ]

            pod_aggs = agg[
                pod_start:
                pod_start + pod_size
            ]

            for esw in pod_edges:

                for asw in pod_aggs:

                    add_link(
                        esw,
                        asw,
                    )

        required_ports = len(agg)

        available_ports = (
            len(core)
            * len(ROUTER_PORTS)
        )

        if required_ports > available_ports:

            raise ValueError(
                "Insufficient router ports for FatTree"
            )

        for i, asw in enumerate(agg):

            add_link(
                asw,
                safe_get(core, i),
            )

        return links

    if topology == "mesh":

        validate_non_empty(
            "edge_switches",
            edge,
        )

        validate_non_empty(
            "agg_switches",
            agg,
        )

        validate_non_empty(
            "core_routers",
            core,
        )

        for i, pc in enumerate(pcs):

            add_link(
                pc,
                edge[
                    min(
                        i // hps,
                        len(edge) - 1,
                    )
                ],
            )

        for i, esw in enumerate(edge):

            add_link(
                esw,
                safe_get(agg, i),
            )

        for i in range(len(agg)):

            for j in range(i + 1, len(agg)):

                add_link(
                    agg[i],
                    agg[j],
                )

        required_ports = len(agg)

        available_ports = (
            len(core)
            * len(ROUTER_PORTS)
        )

        if required_ports > available_ports:

            raise ValueError(
                "Insufficient router ports for Mesh"
            )

        for i, a in enumerate(agg):

            add_link(
                a,
                safe_get(core, i),
            )

        return links

    if topology == "fnn":

        validate_non_empty(
            "zone_switches",
            zone,
        )

        validate_non_empty(
            "gateways",
            gateways,
        )

        validate_non_empty(
            "core_routers",
            core,
        )

        for i, pc in enumerate(pcs):

            add_link(
                pc,
                zone[
                    min(
                        i // hps,
                        len(zone) - 1,
                    )
                ],
            )

        for i, sw in enumerate(zone):

            add_link(
                sw,
                safe_get(gateways, i),
            )

        for gw in gateways:

            add_link(
                gw,
                core[0],
            )

        return links

    return links