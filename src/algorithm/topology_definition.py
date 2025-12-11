class TopologyDefinition:
    def __init__(self, data: dict):
        self.type = data["type"]
        self.name = data["name"]
        self.base_capacity = data["base_capacity"]
        self.dynamic_factor = data["dynamic_factor"]
        self.scalability = data["scalability"]
        self.redundancy = data["redundancy"]
        self.cost = data["cost"]
        self.subBins = data["subBins"]
        self.create_bins = data["create_bins"]
        self.layer_mapping = data["layer_mapping"]
        self.bin_weights = data["bin_weights"]