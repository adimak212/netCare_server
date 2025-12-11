import math

class AlgorithmEngine:

    @staticmethod
    def choose_topology(topologies, templates, s, r, c):
        best = topologies[0]
        best_score = float("inf")

        for topo in topologies:
            capacity_ratio, _ = AlgorithmEngine.is_available(topo, templates)
            dist = AlgorithmEngine.distance(topo, s, r, c)
            score = AlgorithmEngine.final_score(capacity_ratio, dist)

            if score < best_score:
                best = topo
                best_score = score

        return best

    @staticmethod
    def is_available(topology, templates):
        total_weight = sum(
            t["bandwidth"] + t["connections"] + t["processing"]
            for t in templates
        )
        cap = topology.capacity(len(templates))
        return total_weight / cap, total_weight <= cap

    @staticmethod
    def distance(t, s, r, c):
        return math.sqrt(
            (s - t.scalability)**2 +
            (r - t.redundancy)**2 +
            (c - t.cost)**2
        )

    @staticmethod
    def final_score(cap, dist):
        return 0.8 * (1 - dist) + 0.2 * cap
