from typing import List
from datetime import datetime

class BinPackingAllocator:
    @staticmethod
    def allocate(items: List[dict], bins: List) -> dict:

        for item in items:
            item["weight"] = (
                item["bandwidth"] +
                item["connections"] +
                item["processing"]
            )
            item["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")

        items.sort(key=lambda x: x["weight"], reverse=True)

        assignments = {}

        for item in items:
            best_bin = None
            best_residual = float("inf")

            for b in bins:
                if b.can_fit(item["weight"]):
                    residual = b.capacity - (b.used + item["weight"])
                    if residual < best_residual:
                        best_residual = residual
                        best_bin = b

            if not best_bin:
                raise Exception(f"No suitable bin for item {item['id']}")

            best_bin.add(item)
            assignments[item["id"]] = best_bin.id

        return {"bins": bins, "assignments": assignments}
