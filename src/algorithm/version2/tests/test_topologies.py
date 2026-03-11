from src.algorithm.version2.topologies.fat_tree import FatTreeTopology
from src.algorithm.version2.topologies.fnn import FNNTopology
from src.algorithm.version2.topologies.hybrid import HybridTopology
from src.algorithm.version2.topologies.mesh import MeshTopology
from src.algorithm.version2.topologies.sdn import SDNTopology


def main():
    params = {
        "pcs": 12
    }

    topologies = [
        FatTreeTopology(),
        FNNTopology(),
        HybridTopology(),
        MeshTopology(),
        SDNTopology(),
    ]

    for topology in topologies:
        normalized = topology.normalize(params)

        print("=" * 40)
        print("Topology:", topology.key)
        print("Name:", topology.name)
        print("Metrics:", topology.Scalability, topology.Redundancy, topology.Cost)
        print("Normalized:", normalized)


if __name__ == "__main__":
    main()