from typing import Any, Dict, List
from .templates import load_default_templates, load_default_bin_capacities
from .BinFactory import pack_per_bin_type


def physical_cost_for_topology(topo, params, templates, capacities) -> float:
    normalized = topo.normalize(params)
    items = topo.build_items(normalized, templates)
    bins = pack_per_bin_type(items, capacities, {"u": 0.6, "watt": 0.4, "cost": 0.0, "ports": 0.0})
    racks = len(bins)
    unused_u = sum(b.remaining()["u"] for b in bins)
    unused_watt = sum(b.remaining()["watt"] for b in bins)
    
    pcost = (1.0 * racks) + (0.1 * unused_u) + (0.001 * unused_watt)
    return pcost , normalized


def rank_topologies(
    topology_classes: Dict[str, Any],
    params: Dict[str, Any],
    s: float,
    r: float,
    c: float,
) -> List[Dict[str, Any]]:

    templates = load_default_templates()
    capacities = load_default_bin_capacities()

    total = float(s) + float(r) + float(c)
    if total > 0:
        s, r, c = float(s) / total, float(r) / total, float(c) / total
    else:
        s, r, c = 0.0, 0.0, 0.0

    temp: List[Dict[str, Any]] = []
    for topo in topology_classes.values():
        pcost , normalized = physical_cost_for_topology(topo, params, templates, capacities)
        temp.append({"topo": topo, "pcost": pcost})

    min_cost = min(x["pcost"] for x in temp) if temp else 0.0
    max_cost = max(x["pcost"] for x in temp) if temp else 1.0
    den = max_cost - min_cost

    ranked: List[Dict[str, Any]] = []
    for x in temp:
        topo = x["topo"]
        pcost = x["pcost"]

        dynamic_cost = 0.5 if den == 0 else (pcost - min_cost) / den

        score = (
            float(topo.Scalability) * s +
            float(topo.Redundancy)  * r +
            (1.0 - float(dynamic_cost)) * c
        )

        ranked.append({
            "key": topo.key,
            "name": topo.name,
            "score": round(score, 4),
            "debug": {"normalized": normalized},
            "metrics": {
                "scalability": float(topo.Scalability),
                "redundancy": float(topo.Redundancy),
                "cost": round(float(dynamic_cost), 4),
                "physical_cost_raw": round(float(pcost), 4),
            }
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked
