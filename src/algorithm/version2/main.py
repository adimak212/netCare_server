from __future__ import annotations
import json
import sys
from src.algorithm.version2.domain.user_preferences import UserPreferences
from src.algorithm.version2.domain.resources import Resources
from src.algorithm.version2.topologies import (
    FatTreeTopology,
    FNNTopology,
    MeshTopology,
    SDNTopology,
    HybridTopology,
)

from src.algorithm.version2.services.topology_ranker import TopologyRanker
from src.algorithm.version2.services.nodes import build_gns3_nodes, position_nodes
from src.algorithm.version2.services.links import build_links


def build_topologies():
    return [
        FatTreeTopology(),
        FNNTopology(),
        MeshTopology(),
        SDNTopology(),
        HybridTopology(),
    ]


def build_templates():
    return {
        "pc": Resources(u=1, watt=50, cost=200, ports=1),
        "switch": Resources(u=2, watt=120, cost=1500, ports=8),
        "router": Resources(u=4, watt=200, cost=5000, ports=4),
        "controller": Resources(u=2, watt=100, cost=3000, ports=2),
    }


def build_bin_templates():
    return {
        "rack": {
            "u": 12,
            "watt": 1500,
            "cost": 20000,
            "ports": 24,
        }
    }


def build_unit_costs():
    return {
        "pc": 200,
        "switch": 1500,
        "router": 5000,
        "controller": 3000,
    }


def create_preferences(payload: dict) -> UserPreferences:
    return UserPreferences(
        pcs=int(payload.get("pcs", 0)),
        scalability=float(payload.get("scalability", 0)),
        redundancy=float(payload.get("redundancy", 0)),
        cost=float(payload.get("cost", 0)),
    )


TOPOLOGIES = build_topologies()


def main():
    if len(sys.argv) < 2:
        return {"error": "missing input payload"}

    payload = json.loads(sys.argv[1])
    choice = payload.get("choice")

    if choice == "bestfit":
        preferences = create_preferences(payload)

        params = {
            "pcs": preferences.pcs,
            "hosts_per_switch": int(payload.get("hosts_per_switch", 4)),
            "pcs_per_zone": int(payload.get("pcs_per_zone", 4)),
            "zones_per_gateway": int(payload.get("zones_per_gateway", 3)),
            "switches_per_controller": int(payload.get("switches_per_controller", 50)),
        }

        templates = build_templates()
        bin_templates = build_bin_templates()
        unit_costs = build_unit_costs()
        ranker = TopologyRanker(
            templates=templates,
            bin_templates=bin_templates,
        )

        rank_payload = {
            "params": params,
            "preferences": preferences,
            "unit_costs": unit_costs,
        }
        ranked = ranker.rank(rank_payload)

        response = {
            "input": payload,
            "best_topology": None,
            "ranks": [],
            "errors": [],
        }

        for item in ranked:
            if "error" in item:
                response["errors"].append({
                    "key": item.get("key"),
                    "name": item.get("name"),
                    "error": item.get("error"),
                })
                continue

            response["ranks"].append({
                "key": item["key"],
                "name": item["name"],
                "normalized": item["normalized"],
                "final_score": item["final_score"],
                "waste": item["waste"],
            })

        if response["ranks"]:
            response["best_topology"] = response["ranks"][0]

        if response["ranks"]:
            response["best_topology"] = response["ranks"][0]
        else:
            response["best_topology"] = None

        return response

    if choice == "createNodes":
        node_type_by_type = {
            "pcs": "vpcs",
            "edge_switches": "ethernet_switch",
            "agg_switches": "ethernet_switch",
            "core_routers": "dynamips",
            "zone_switches": "ethernet_switch",
            "gateways": "ethernet_switch",
        }

        topo = next((t for t in TOPOLOGIES if t.name == payload["topology"]), None)
        if topo is None:
            raise ValueError(f"Unknown topology: {payload['topology']}")

        data = json.loads(payload["normalized"]) if isinstance(payload.get("normalized"), str) else payload.get("normalized", {})
        nodes = build_gns3_nodes(data, node_type_by_type)
        positioned_nodes = position_nodes(nodes)
        links = build_links(nodes, topo.key)

        return {"nodes": positioned_nodes, "links": links}

    return {"error": f"Unknown choice: {choice}"}


if __name__ == "__main__":
    out = main()
    sys.stdout.write(json.dumps(out, ensure_ascii=False))