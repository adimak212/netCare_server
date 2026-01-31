from typing import Dict
from .models import Dims

def load_default_templates() -> Dict[str, Dims]:
    return {
        # Office / Lab PC
        "pc": {
            "u": 0,              
            "watt": 65,          
            "cost": 800,        
            "ports": 1
        },

        # Cisco Catalyst 9300-48T (Access Switch)
        "edge_switch": {
            "u": 1,              
            "watt": 95,          
            "cost": 4500,        
            "ports": 48
        },

        # Aggregation – same hardware, higher utilization
        "agg_switch": {
            "u": 1,              
            "watt": 120,         
            "cost": 5000,
            "ports": 48
        },

        # Cisco ASR 1001-X (Core Router)
        "core_router": {
            "u": 1,              
            "watt": 250,         
            "cost": 16000,      
            "ports": 8           
        },

        # SDN Controller – 1U Server (e.g. Dell R640 class)
        "sdn_controller": {
            "u": 1,              
            "watt": 300,         
            "cost": 6000,        
            "ports": 4          
        }
    }

def load_default_bin_capacities() -> Dict[str, Dims]:
    return {
        "core_rack": {"u": 10, "watt": 1500, "cost": 10**9, "ports": 10**9},
        "zone_rack": {"u": 10, "watt": 1500, "cost": 10**9, "ports": 10**9},
        "ctrl_rack": {"u": 10, "watt": 1500, "cost": 10**9, "ports": 10**9},
    }
