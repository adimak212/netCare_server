from src.algorithm.version2.solvers.pattern_generator import PatternGenerator
from src.algorithm.version2.domain.resources import Resources


def main():

    templates = {
        "pc": Resources(u=1, watt=50, cost=200, ports=1),
        "switch": Resources(u=2, watt=120, cost=1500, ports=8),
        "router": Resources(u=4, watt=200, cost=5000, ports=4),
    }

    racks = {
        "rack": {
            "u": 12,
            "watt": 1500,
            "cost": 20000,
            "ports": 24
        }
    }

    generator = PatternGenerator(templates, racks)

    patterns = generator.generate_for_bin_type("rack")

    #("patterns:", len(patterns))

    for p in patterns[:10]:
        #(p.as_dict())


if __name__ == "__main__":
    main()