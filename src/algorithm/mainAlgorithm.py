import json
import sys
from topology import TopologyManager
from bin_builder import BinBuilder
from bin_packing_allocator import BinPackingAllocator
from algorithm_engine import AlgorithmEngine
from topology_definition import TopologyDefinition
from TopologiesSubBins import TOPOLOGY_DEFINITIONS
from TemplateManager import TemplateManager
from graphBuilder import GraphBuilder
import copy

def main(params):
    TemplateManager.init("src/data/templates.json")
    TopologyManager.init("src/data/topologies.json")

    ids = params.get("components[]", [])
    s = float(params.get("scalability", 0)) / 100
    r = float(params.get("redundancy", 0)) / 100
    c = float(params.get("cost", 0)) / 100

    templates = [copy.deepcopy(TemplateManager.get(tid)) for tid in ids]

    topologies = TopologyManager.all()
    best = AlgorithmEngine.choose_topology(topologies, templates, s, r, c)

    definition = TOPOLOGY_DEFINITIONS[best.type]

    bins = BinBuilder.build(len(templates), best, definition)
    result = BinPackingAllocator.allocate(templates, bins)

    nodes = GraphBuilder.bin_to_nodes(result=result)
    print(nodes)


if __name__ == "__main__":
    params = json.loads(sys.argv[1])
    main(params)
