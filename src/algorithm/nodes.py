from typing import Any, Dict, List
from collections import Counter

Node = Dict[str, Any]

layer_to_number = {
    "pcs": 4, 
    "edge_switches": 3, 
    "agg_switches": 2, 
    "core_routers": 1,
    "controllers": 2,
    "zone_switches" : 3,
    "gateways" : 2
}

def build_gns3_nodes(items: Dict[str, int], node_type_by_type: Dict[str, str]) -> List[Node]:
    nodes: List[Node] = []
    idx = 0
    layers_to_names = {
        "pcs": "pc", 
        "edge_switches": "edge_switch", 
        "agg_switches": "agg_switch", 
        "core_routers": "router",
        "zone_switches": "zone_switch",
        "gateways" : "gateway"
    }
    for layer, amount in items.items():
        if layer in node_type_by_type:
            for i in range(int(amount or 0)):
                nodes.append({
                    "name": f"{layers_to_names[layer]}_{i}",
                    "node_type": node_type_by_type[layer],
                    "layer": layer,
                    "index": idx,
                })
                idx += 1

    return nodes


def position_nodes(nodes: List[Node]):
    base_x = 100
    base_y = 80

    num_for_layer_x = Counter(node["layer"] for node in nodes)
    counter = Counter(node["layer"] for node in nodes)

    new_nodes: List[Node] = []

    for node in nodes:
        base_x = 1000 / (counter[node["layer"]] + 1)
        node["x"] = base_x * num_for_layer_x[node["layer"]]
        num_for_layer_x[node["layer"]] -= 1

        node["y"] = base_y * layer_to_number[node["layer"]]

        new_nodes.append(node)

    return new_nodes

