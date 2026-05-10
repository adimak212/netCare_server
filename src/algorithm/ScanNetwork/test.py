import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from netCareScanner import NetCareScanner

async def debug():
    scanner = NetCareScanner("admin", "1234", "10.10.10.0/24")
    await scanner.scan_device("10.10.10.1", "Core-Router")
    
    print("=== ARP TABLE ===")
    for ip, mac in scanner.arp_table.items():
        print(f"  {ip} -> {mac}")
    
    print("\n=== SWITCH MAC TABLES ===")
    for sw, table in scanner.switch_mac_tables.items():
        print(f"  Switch {sw}:")
        for mac, port in table.items():
            print(f"    {mac} -> {port}")
    
    print("\n=== DEVICES BEFORE finalize ===")
    for ip, d in scanner.devices.items():
        print(f"  {ip}: {d}")
    
    scanner.finalize_pcs()
    
    print("\n=== DEVICES AFTER finalize ===")
    for ip, d in scanner.devices.items():
        print(f"  {ip}: {d}")

asyncio.run(debug())