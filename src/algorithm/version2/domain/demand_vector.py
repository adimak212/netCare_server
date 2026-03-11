from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class DemandVector:
    pc: int = 0
    switch: int = 0
    router: int = 0
    controller: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "pc": self.pc,
            "switch": self.switch,
            "router": self.router,
            "controller": self.controller,
        }

    def __add__(self, other: "DemandVector") -> "DemandVector":
        return DemandVector(
            pc=self.pc + other.pc,
            switch=self.switch + other.switch,
            router=self.router + other.router,
            controller=self.controller + other.controller,
        )

    def __sub__(self, other: "DemandVector") -> "DemandVector":
        return DemandVector(
            pc=self.pc - other.pc,
            switch=self.switch - other.switch,
            router=self.router - other.router,
            controller=self.controller - other.controller,
        )

    def clamp_non_negative(self) -> "DemandVector":
        return DemandVector(
            pc=max(0, self.pc),
            switch=max(0, self.switch),
            router=max(0, self.router),
            controller=max(0, self.controller),
        )

    def is_zero(self) -> bool:
        return (
            self.pc == 0 and
            self.switch == 0 and
            self.router == 0 and
            self.controller == 0
        )

    def total_items(self) -> int:
        return self.pc + self.switch + self.router + self.controller

    def scale(self, factor: int) -> "DemandVector":
        return DemandVector(
            pc=self.pc * factor,
            switch=self.switch * factor,
            router=self.router * factor,
            controller=self.controller * factor,
        )
        
    