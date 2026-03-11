from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class Resources:
    u: int = 0
    watt: int = 0
    cost: int = 0
    ports: int = 0

    def __add__(self, other: "Resources") -> "Resources":
        return Resources(
            u=self.u + other.u,
            watt=self.watt + other.watt,
            cost=self.cost + other.cost,
            ports=self.ports + other.ports
        )

    def __iadd__(self, other: "Resources") -> "Resources":
        self.u += other.u
        self.watt += other.watt
        self.cost += other.cost
        self.ports += other.ports
        return self

    def __mul__(self, factor: int) -> "Resources":
        return Resources(
            u=self.u * factor,
            watt=self.watt * factor,
            cost=self.cost * factor,
            ports=self.ports * factor
        )

    def fits_in(self, capacity: "Resources") -> bool:
        return (
            self.u <= capacity.u
            and self.watt <= capacity.watt
            and self.ports <= capacity.ports
        )

    def as_dict(self) -> dict:
        return {
            "u": self.u,
            "watt": self.watt,
            "cost": self.cost,
            "ports": self.ports
        }