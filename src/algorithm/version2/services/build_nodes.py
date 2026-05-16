from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

from ..models.models import Item

Node = Dict[str, Any]


def build_nodes(
    items: List[Item],
) -> List[Node]:

    nodes: List[Node] = []

    for index, item in enumerate(items):

        node_type = _resolve_node_type(
            item.item_type
        )

        nodes.append({
            "id": str(uuid4()),
            "index": index,
            "name": item.id,
            "label": item.id,
            "node_type": node_type,
            "layer": _resolve_layer(
                item.layer
            ),
            "item_type": item.item_type,
            "x": 0,
            "y": 0,
        })

    return nodes


def _resolve_node_type(
    item_type: str,
) -> str:

    if "router" in item_type:
        return "dynamips"

    if "switch" in item_type:
        return "ethernet_switch"

    if (
        "pc" in item_type or
        "host" in item_type
    ):
        return "vpcs"

    if "controller" in item_type:
        return "cloud"

    return "ethernet_switch"


def _resolve_layer(
    layer: str,
) -> str:

    mapping = {
        "core": "core_routers",
        "aggregation": "agg_switches",
        "edge": "edge_switches",
        "host": "pcs",
        "controller": "controllers",
    }

    return mapping.get(layer, layer)