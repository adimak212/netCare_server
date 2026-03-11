from __future__ import annotations

from dataclasses import dataclass

from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.domain.resources import Resources


@dataclass(frozen=True)
class Pattern:
    bin_type: str
    counts: DemandVector
    total_resources: Resources
    bin_capacity: Resources

    def total_items(self) -> int:
        return self.counts.total_items()

    def signature(self) -> str:
        return (
            f"{self.bin_type}|"
            f"pc:{self.counts.pc}|"
            f"sw:{self.counts.switch}|"
            f"rt:{self.counts.router}|"
            f"ctrl:{self.counts.controller}"
        )

    def utilization_ratios(self) -> dict:
        return {
            "u": (self.total_resources.u / self.bin_capacity.u) if self.bin_capacity.u else 0.0,
            "watt": (self.total_resources.watt / self.bin_capacity.watt) if self.bin_capacity.watt else 0.0,
            "ports": (self.total_resources.ports / self.bin_capacity.ports) if self.bin_capacity.ports else 0.0,
            "cost": (self.total_resources.cost / self.bin_capacity.cost) if self.bin_capacity.cost else 0.0,
        }

    def as_dict(self) -> dict:
        return {
            "bin_type": self.bin_type,
            "counts": self.counts.as_dict(),
            "total_resources": {
                "u": self.total_resources.u,
                "watt": self.total_resources.watt,
                "cost": self.total_resources.cost,
                "ports": self.total_resources.ports,
            },
            "bin_capacity": {
                "u": self.bin_capacity.u,
                "watt": self.bin_capacity.watt,
                "cost": self.bin_capacity.cost,
                "ports": self.bin_capacity.ports,
            },
            "utilization": self.utilization_ratios(),
        }