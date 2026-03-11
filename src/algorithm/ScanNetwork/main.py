from scan import scan_by_arp
from classification import classify_devices, filter_network_devices
from snmp import snmp_basic_info
from fingerprint import classify_from_fingerprint

CIDR = "192.168.1.0/24"
LOCAL_IP = "192.168.1.106"
GATEWAY_IP = "192.168.1.1"


import subprocess
import re
import ipaddress

import subprocess
import json
import ipaddress

def get_network_context_windows():
    ps = r"""
    $cfg = Get-NetIPConfiguration |
      Where-Object { $_.IPv4Address -ne $null -and $_.NetProfile -ne $null } |
      Select-Object InterfaceAlias,
                    @{n='IPv4';e={$_.IPv4Address.IPAddress}},
                    @{n='PrefixLength';e={$_.IPv4Address.PrefixLength}},
                    @{n='Gateway';e={ if ($_.IPv4DefaultGateway) { $_.IPv4DefaultGateway.NextHop } else { $null } }},
                    @{n='InterfaceMetric';e={$_.NetIPv4Interface.InterfaceMetric}},
                    @{n='ProfileCategory';e={$_.NetProfile.NetworkCategory}} |
      ConvertTo-Json -Depth 3
    $cfg
    """
    out = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", ps],
        text=True,
        encoding="utf-8",
        errors="ignore",
    ).strip()

    if not out:
        raise RuntimeError("PowerShell returned empty output")

    data = json.loads(out)

    if isinstance(data, dict):
        items = [data]
    else:
        items = data

    candidates = []
    for it in items:
        ipv4 = it.get("IPv4")
        prefix = it.get("PrefixLength")
        gw = it.get("Gateway")
        metric = it.get("InterfaceMetric")

        if not ipv4 or prefix is None:
            continue
        if ipv4.startswith("169.254."): 
            continue
        score = 0
        if gw:
            score += 100
        if isinstance(metric, int):
            score += max(0, 50 - min(metric, 50))

        network = ipaddress.IPv4Network(f"{ipv4}/{int(prefix)}", strict=False)
        cidr = str(network)

        candidates.append((score, ipv4, gw, cidr, it.get("InterfaceAlias")))

    if not candidates:
        raise RuntimeError("Could not detect IPv4 network context via PowerShell")

    candidates.sort(reverse=True, key=lambda x: x[0])
    _, local_ip, gateway_ip, cidr, iface = candidates[0]

    if not gateway_ip:
        gateway_ip = ""

    return local_ip, gateway_ip, cidr

def main():
    local_ip, gateway_ip, cidr = get_network_context_windows()
    print(f"Using iface context: local_ip={local_ip}, gateway={gateway_ip}, cidr={cidr}")
    print("🔎 Running ARP scan...")
    
    devices = scan_by_arp(cidr, local_ip=local_ip, timeout=2)

    print(f"Found {len(devices)} devices\n")

    classified = classify_devices(
        devices,
        oui_csv_path="files/oui.csv",
        gateway_ip=gateway_ip
    )

    for d in classified:
        ip = d["ip"]
        vendor = d["vendor"]

        snmp_info = snmp_basic_info(ip)  # פעם אחת
        if snmp_info:
            print("SNMP ENABLED")
            print("sysName:", snmp_info.get("sysName"))

        print(f"\nDevice: {ip}")
        print("Vendor:", vendor)
        print("Category:", d["category"], "Confidence:", d["confidence"])

        if snmp_info:
            print("SNMP sysName:", snmp_info.get("sysName"))
            sysdescr = snmp_info.get("sysDescr") or ""
            print("SNMP sysDescr:", sysdescr[:100])

        role = classify_from_fingerprint(ip, vendor, is_gateway=(ip == gateway_ip))
        if role:
            print("Role:", role)


if __name__ == "__main__":
    main()
