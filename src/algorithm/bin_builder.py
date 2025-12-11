from typing import List
from bin import Bin

class BinBuilder:
    @staticmethod
    def build(num_devices: int, topology, definition) -> List[Bin]:
        bin_structure = definition.create_bins(num_devices)
        total_capacity = topology.capacity(num_devices)

        total_weight = sum(
            definition.bin_weights[b] * count
            for b, count in bin_structure.items()
        )

        bins = []

        for bin_type, count in bin_structure.items():
            weight = definition.bin_weights[bin_type]
            sub_capacity = (total_capacity * weight) / total_weight
            layer = definition.layer_mapping.get(bin_type)

            for i in range(count):
                bins.append(
                    Bin(
                        id=f"{bin_type}_{i}",
                        type=bin_type,
                        capacity=sub_capacity,
                        layer=layer
                    )
                )
        return bins
