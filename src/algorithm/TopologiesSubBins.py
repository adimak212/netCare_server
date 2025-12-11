from math import ceil
from topology_definition import TopologyDefinition

def create_bins_fat_tree(num_devices: int):
    pods = ceil(num_devices / 20)
    return {
        "pod": pods,
        "access_block": pods * 4,
        "aggregation_block": pods * 2
    }

FAT_TREE_DEFINITION = {
    "type": "fat_tree",
    "name": "Fat Tree",
    "base_capacity": 25000,
    "dynamic_factor": 150,
    "scalability": 0.90,
    "redundancy": 0.80,
    "cost": 0.50,
    "subBins": ["pod", "access_block", "aggregation_block"],
    "create_bins": create_bins_fat_tree,
    "layer_mapping": {
        "pod": "aggregation",
        "access_block": "access",
        "aggregation_block": "aggregation"
    },
    "bin_weights": {
        "access_block": 1,
        "aggregation_block": 3,
        "pod": 6
    }
}


def create_bins_mesh(num_devices: int):
    zones = ceil(num_devices / 10)
    return {
        "zone": zones
    }

MESH_DEFINITION = {
    "type": "mesh",
    "name": "Mesh",
    "base_capacity": 20000,
    "dynamic_factor": 130,
    "scalability": 0.70,
    "redundancy": 0.90,
    "cost": 0.70,
    "subBins": ["zone"],
    "create_bins": create_bins_mesh,
    "layer_mapping": {
        "zone": "flat"
    },
    "bin_weights": {
        "zone": 1
    }
}


def create_bins_fnn(num_devices: int):
    neighborhoods = ceil(num_devices / 8)
    return {
        "neighborhood": neighborhoods
    }

FNN_DEFINITION = {
    "type": "fnn",
    "name": "Flat Neighborhood Network",
    "base_capacity": 15000,
    "dynamic_factor": 80,
    "scalability": 0.50,
    "redundancy": 0.30,
    "cost": 0.30,
    "subBins": ["neighborhood"],
    "create_bins": create_bins_fnn,
    "layer_mapping": {
        "neighborhood": "flat"
    },
    "bin_weights": {
        "neighborhood": 1
    }
}


def create_bins_hybrid(num_devices: int):
    segments = ceil(num_devices / 15)
    return {
        "core_zone": 1,
        "segment": segments
    }

HYBRID_DEFINITION = {
    "type": "hybrid",
    "name": "Hybrid",
    "base_capacity": 22000,
    "dynamic_factor": 120,
    "scalability": 0.70,
    "redundancy": 0.60,
    "cost": 0.40,
    "subBins": ["core_zone", "segment"],
    "create_bins": create_bins_hybrid,
    "layer_mapping": {
        "core_zone": "core",
        "segment": "access"
    },
    "bin_weights": {
        "core_zone": 5,
        "segment": 1
    }
}


def create_bins_sdn(num_devices: int):
    segments = ceil(num_devices / 25)
    return {
        "segment": segments
    }

SDN_DEFINITION = {
    "type": "sdn",
    "name": "Software Defined Network",
    "base_capacity": 30000,
    "dynamic_factor": 180,
    "scalability": 0.85,
    "redundancy": 0.80,
    "cost": 0.40,
    "subBins": ["segment"],
    "create_bins": create_bins_sdn,
    "layer_mapping": {
        "segment": "switching"
    },
    "bin_weights": {
        "segment": 1
    }
}


TOPOLOGY_DEFINITIONS = {
    "fat_tree": TopologyDefinition(FAT_TREE_DEFINITION),
    "mesh": TopologyDefinition(MESH_DEFINITION),
    "fnn": TopologyDefinition(FNN_DEFINITION),
    "hybrid": TopologyDefinition(HYBRID_DEFINITION),
    "sdn": TopologyDefinition(SDN_DEFINITION)
}

