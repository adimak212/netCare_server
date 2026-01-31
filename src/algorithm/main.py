import json
import sys
from uuid import uuid4
from typing import Dict, Any, List, Literal, Tuple
from .compare import rank_topologies
from .templates import load_default_templates, load_default_bin_capacities
from .topologies import TOPOLOGIES
from .BinFactory import pack_per_bin_type

def bins_to_dict(bins):
    return [
        {
            "id": b.id,
            "type": b.bin_type,
            "used": b.used,
            "capacity": b.capacity,
            "remaining": b.remaining(),
            "items": [
                {"id": it.id, "type": it.item_type, "layer": it.layer, "size": it.size}
                for it in b.items
            ],
        }
        for b in bins
    ]

Node = Dict[str, Any]

def build_gns3_nodes(items: Dict[str, int], node_type_by_type: Dict[str, str]) -> List[Node]:
    nodes: List[Node] = []
    idx = 0
    for layer, amount in items.items():
        if layer in node_type_by_type :
            for i in range(int(amount or 0)):
                nodes.append({
                    "name": f"{layer}_{i}",
                    "node_type": node_type_by_type[layer],
                    "layer": layer,
                    "index": idx,
                })
                idx += 1
    return nodes


Link = Dict[str, Any]
Topology = Literal["fat_tree", "mesh", "sdn", "fnn", "hybrid"]


def build_links(
    nodes: List[Node],
    topology: str,
    *,
    hosts_per_switch: int = 2,
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
        node = node_by_name[node_name]
        nt = node["node_type"]

        if nt == "vpcs":
            pool = [{"adapter_number": 0, "port_number": 0, "port": "e0"}]
        elif nt == "ethernet_switch":
            pool = [{"adapter_number": 0, "port_number": i, "port": f"e{i}"} for i in range(switch_ports)]
        elif nt == "cloud":
            pool = [{"adapter_number": 0, "port_number": i, "port": f"e{i}"} for i in range(cloud_ports)]
        elif nt == "dynamips":
            pool = [{"adapter_number": a, "port_number": p, "port": l} for a, p, l in ROUTER_PORTS]
        else:
            pool = [{"adapter_number": 0, "port_number": i, "port": f"e{i}"} for i in range(switch_ports)]

        port_pool[node_name] = pool
        port_idx[node_name] = 0
        used_ports[node_name] = set()

    def alloc_port(node_name: str) -> Dict[str, Any]:
        init_pool(node_name)
        pool = port_pool[node_name]
        n = len(pool)
        for k in range(n):
            i = (port_idx[node_name] + k) % n
            cand = pool[i]
            key = (cand["adapter_number"], cand["port_number"])
            if key not in used_ports[node_name]:
                used_ports[node_name].add(key)
                port_idx[node_name] = (i + 1) % n
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

    topology = topology.lower().strip()

    if topology == "mesh":
        if not pcs or not edge or not agg or not core:
            raise ValueError(f"mesh requires layers pcs, edge_switches, agg_switches, core_routers. got: pcs={len(pcs)} edge={len(edge)} agg={len(agg)} core={len(core)}")

        hps = max(1, int(hosts_per_switch))

        for i, pc in enumerate(pcs):
            esw = edge[min(i // hps, len(edge) - 1)]
            add_link(pc, esw)

        access_uplinks = 2
        for i, esw in enumerate(edge):
            b1 = agg[i % len(agg)]
            add_link(esw, b1)
            if access_uplinks >= 2 and len(agg) > 1:
                b2 = agg[(i + 1) % len(agg)]
                if b2 != b1:
                    add_link(esw, b2)

        if len(agg) <= 4:
            for i in range(len(agg)):
                for j in range(i + 1, len(agg)):
                    add_link(agg[i], agg[j])
        else:
            for i in range(len(agg)):
                add_link(agg[i], agg[(i + 1) % len(agg)])

        for i, bsw in enumerate(agg):
            add_link(bsw, core[i % len(core)])

        return links


    if topology == "fat_tree":
        for i, pc in enumerate(pcs):
            add_link(pc, edge[i // hosts_per_switch])
        uplinks_per_edge = 2
        for i in range(0, len(edge), 2):
            e = edge[i]
            e_2 = edge[i + 1] 
            for k in range(min(uplinks_per_edge, len(agg))):
                a = agg[(i + k) % len(agg)]
                add_link(e, a)
                add_link(e_2 , a)   
                
       
        for i, a in enumerate(agg):
            cnode = core[i % len(core)]
            add_link(a, cnode)

        return links

    if topology == "fnn":
        seq = [pcs, edge, agg, core]
        for i in range(len(seq) - 1):
            for a in seq[i]:
                for b in seq[i + 1]:
                    add_link(a, b)
        return links

    raise ValueError(f"Unknown topology '{topology}'")


def main(params: Dict[str, Any]):
    choice = params.get("choice")
    if choice == "bestfit":
        s = float(params.get("scalability", 0))
        r = float(params.get("redundancy", 0))
        c = float(params.get("cost", 0))
        #print(s, " " ,r , " ",c)
        ranked = rank_topologies(
            TOPOLOGIES,
            params,
            s=s , r=r , c=c
        )
        return {"ranks": ranked}
    
    if choice == "build":
        topo = TOPOLOGIES[params["topology"]]
        templates = load_default_templates()
        capacities = load_default_bin_capacities()
        normalized = topo.normalize(params)
        items = topo.build_items(normalized, templates)
        bins = pack_per_bin_type(items, capacities, {"u": 0.6, "watt": 0.4})
        
        return {
            "topology": {"key": topo.key, "name": topo.name},
            "normalized": normalized,
            "packing": {"binsUsed": len(bins), "bins": bins_to_dict(bins)},
        }

    if choice == "createNodes":
        node_type_by_type = {
            "pcs": "vpcs",
            "edge_switches": "ethernet_switch",
            "agg_switches": "ethernet_switch",
            "core_routers": "dynamips",
        }
        topo = TOPOLOGIES[params["topology"]]
        data = json.loads(params["normalized"]) if isinstance(params.get("normalized"), str) else params.get("normalized", {})
        #print (data)
        nodes = build_gns3_nodes(data, node_type_by_type)
        links = build_links(nodes, topo.key)
        return {"nodes": nodes, "links": links}

    raise ValueError(f"Unknown choice '{choice}'")


if __name__ == "__main__":
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    out = main(params)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
