from src.algorithm.version2.domain.resources import Resources
from src.algorithm.version2.domain.pattern import Pattern
from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.solvers.pattern_solver import PatternSolver


def main():
    patterns = [
        Pattern(
            bin_type="rack",
            counts=DemandVector(pc=4, switch=2, router=1, controller=0),
            total_resources=Resources(u=12, watt=600, cost=8000, ports=20),
        ),
        Pattern(
            bin_type="rack",
            counts=DemandVector(pc=2, switch=3, router=1, controller=0),
            total_resources=Resources(u=12, watt=650, cost=8500, ports=22),
        ),
        Pattern(
            bin_type="rack",
            counts=DemandVector(pc=6, switch=1, router=0, controller=0),
            total_resources=Resources(u=10, watt=500, cost=5000, ports=14),
        ),
        Pattern(
            bin_type="rack",
            counts=DemandVector(pc=0, switch=1, router=0, controller=0),
            total_resources=Resources(u=2, watt=120, cost=1500, ports=8),
        ),
        Pattern(
            bin_type="rack",
            counts=DemandVector(pc=0, switch=0, router=1, controller=0),
            total_resources=Resources(u=4, watt=200, cost=5000, ports=4),
        ),
        Pattern(
            bin_type="rack",
            counts=DemandVector(pc=1, switch=0, router=0, controller=0),
            total_resources=Resources(u=1, watt=50, cost=200, ports=1),
        ),
    ]

    demand = DemandVector(pc=12, switch=8, router=4, controller=0)

    solver = PatternSolver(patterns)
    result = solver.solve(demand)

    #(result.as_dict())


if __name__ == "__main__":
    main()