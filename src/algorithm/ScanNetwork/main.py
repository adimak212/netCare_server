import asyncio
import json
import sys
import os

# וודא שהייבוא עובד מתוך התיקייה
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from netCareScanner import NetCareScanner
from TopologyManager import TopologyManager
async def main():
    try:
        if len(sys.argv) < 2: return
        data = json.loads(sys.argv[1])
        
        scanner = NetCareScanner(data.get("userName", "admin"), data.get("password", "1234"), data.get("network", "10.10.10.0/24"))
        await scanner.scan_device(data.get("start_ip", "10.10.10.1"), "Core-Router")
        scanner.finalize_pcs()
        
        if scanner.devices_list:
            TopologyManager.apply_force_layout(scanner.devices_list, scanner.links_list)
        
            nodes, conns = TopologyManager.create_final_topology(
                scanner.devices_list,
                scanner.links_list,
                scanner.switch_mac_tables
            )
            
            result = {"canvasComponnents": nodes, "connections": conns}
            print(json.dumps(result)) # ההדפסה היחידה
            
            with open("topology_data.json", "w") as f:
                json.dump(result, f, indent=4)
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    asyncio.run(main())