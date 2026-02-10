import json
import sys
from uuid import uuid4
from typing import Dict, Any, List, Literal, Tuple
from .compare import rank_topologies
from .templates import load_default_templates, load_default_bin_capacities
from .topologies import TOPOLOGIES
from .BinFactory import pack_per_bin_type
from .serialization import bins_to_dict
from .nodes import build_gns3_nodes, position_nodes
from .links import build_links


def main(params: Dict[str, Any]):
    choice = params.get("choice")
    if choice == "bestfit":
        s = float(params.get("scalability", 0))
        r = float(params.get("redundancy", 0))
        c = float(params.get("cost", 0))
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
            "items" : items,
            "packing": {"binsUsed": len(bins), "bins": bins_to_dict(bins)},
        }

    if choice == "createNodes":
        node_type_by_type = {
            "pcs": "vpcs",
            "edge_switches": "ethernet_switch",
            "agg_switches": "ethernet_switch",
            "core_routers": "dynamips",
            "zone_switches": "ethernet_switch",
            "gateways": "ethernet_switch",
        }
        topo = TOPOLOGIES[params["topology"]]
        data = json.loads(params["normalized"]) if isinstance(params.get("normalized"), str) else params.get("normalized", {})
        nodes = build_gns3_nodes(data, node_type_by_type)
        positioned_nodes = position_nodes(nodes)
        #print(positioned_nodes)
        links = build_links(nodes, topo.key)
        return {"nodes": positioned_nodes, "links": links}

    raise ValueError(f"Unknown choice '{choice}'")

if __name__ == "__main__":
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    out = main(params)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
