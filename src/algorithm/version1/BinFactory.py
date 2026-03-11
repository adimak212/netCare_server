from typing import List , Dict
from .models import Bin
from .packer import best_fit_decreasing

class BinFactory:
    def __init__(self, bin_type: str, capacity: Dict[str, float]):
        self.bin_type = bin_type
        self.capacity = capacity
        self.i = 0

    def __call__(self) -> Bin:
        self.i += 1
        return Bin(id=f"{self.bin_type}_{self.i}", bin_type=self.bin_type, capacity=dict(self.capacity))


def pack_per_bin_type(items, caps, score_weights):
    grouped = {"core_rack": [], "zone_rack": [], "ctrl_rack": []}
    for it in items:
        grouped[it.allowed_bin_types[0]].append(it)

    bins: List[Bin] = []
    for bin_type, its in grouped.items():
        if its:
            factory = BinFactory(bin_type, caps[bin_type])
            bins.extend(best_fit_decreasing(its, factory, score_weights))

    return bins
