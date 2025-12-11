from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class GraphBuilder : 
    
    def bin_to_nodes(result) :
        bins = result["bins"]
        nodes = []
        x_offset = 200
        y_offset = 200
        layer_height = 300
        
        for bin in bins :
            layer = bin.layer
            x = x_offset
            y = y_offset + (layer_height * hash(layer) % 3) 
            
            for index , comp in enumerate(bin.components):
                node = {
                    "node_id": comp["id"],
                    "type": comp["type"],
                    "name": comp["name"],
                    "bin": bin.id,
                    "layer": layer,
                    "x": x + (index % 10) * 150,
                    "y": y + (index // 10) * 150
                }
                nodes.append(node)
        return nodes    