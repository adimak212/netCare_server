from src.algorithm.version2.topologies.fat_tree import FatTreeTopology


def main():

    topology = FatTreeTopology()

    params = {"pcs": 12}

    normalized = topology.normalize(params)

    demand = topology.to_pattern_demand(normalized)

    print(normalized)
    print(demand.as_dict())


if __name__ == "__main__":
    main()