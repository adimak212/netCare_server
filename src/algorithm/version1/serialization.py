from typing import Any, Dict, List
from .models import Bin


def bins_to_dict(bins: List[Bin]) -> List[Dict[str, Any]]:
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
