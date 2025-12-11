
from TopologyManeger import TopologyManager, Topology
class AlgorithmEngine:
    @staticmethod
    def choose_topology(topologies, templates, s, r, c):
        best = topologies[0]
        best_score = float("inf")

        for topo in topologies:
            capacity_ratio, ok = AlgorithmEngine.isAvailable(topo, templates)
            dist = AlgorithmEngine.distance(topo, s, r, c)
            score = AlgorithmEngine.finalScore(capacity_ratio, dist)

            if score < best_score:
                best = topo
                best_score = score

        return best

    @staticmethod
    def isAvailable(topology: Topology, templates):
        total_weight = sum(
            t["bandwidth"] + t["connections"] + t["processing"]
            for t in templates
        )
        cap = topology.capacity(len(templates))
        return total_weight / cap, total_weight <= cap

    @staticmethod
    def distance(t: Topology, s, r, c):
        import math
        return math.sqrt(
            (s - t.scalability) ** 2 +
            (r - t.redundancy) ** 2 +
            (c - t.cost) ** 2
        )

    @staticmethod
    def finalScore(cap, dist):
        return 0.8 * (1 - dist) + 0.2 * cap
