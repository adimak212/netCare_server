from __future__ import annotations
from typing import Callable, List, Optional
from .models import Bin, Item, Dims, add_dims, sub_dims

def sort_key(item: Item, weights: Dims) -> float:
    return sum(weights.get(dim, 0.0) * float(item.size.get(dim, 0.0)) for dim in weights)

def slack_score(remaining_after: Dims, capacity: Dims, weights: Dims) -> float:
    score = 0.0
    for dim, w in weights.items():
        cap = capacity.get(dim, 0.0)
        if cap <= 0:
            continue
        score += w * (remaining_after.get(dim, 0.0) / cap)
    return score

def best_fit_decreasing(items: List[Item], bin_factory: Callable[[], Bin], score_weights: Dims) -> List[Bin]:
    items_sorted = sorted(items, key=lambda it: sort_key(it, score_weights), reverse=True)
    bins: List[Bin] = []

    for item in items_sorted:
        best_idx: Optional[int] = None
        best_sc = float("inf")

        for i, b in enumerate(bins):
            if not b.can_accept(item):
                continue
            used_after = add_dims(b.used, item.size)
            rem_after = sub_dims(b.capacity, used_after)
            sc = slack_score(rem_after, b.capacity, score_weights)
            if sc < best_sc:
                best_sc = sc
                best_idx = i

        if best_idx is None:
            new_bin = bin_factory()
            if not new_bin.can_accept(item):
                raise ValueError(
                    f"Item {item.id} doesn't fit in an empty bin {new_bin.bin_type}. "
                    f"item.size={item.size} bin.cap={new_bin.capacity}"
                )
            new_bin.add(item)
            bins.append(new_bin)
        else:
            bins[best_idx].add(item)

    return bins
