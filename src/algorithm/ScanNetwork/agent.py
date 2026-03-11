import json
import uuid
import time
import pathlib
import subprocess
import ipaddress
import requests
from datetime import datetime, timezone

from scan import scan_by_arp
from classification import classify_devices

CONFIG_PATH = pathlib.Path("agent_config.json")

SERVER_URL = "http://localhost:3000/v1/agents/report"
API_KEY = "netcare_local_secret"  

def load_or_create_agent_id() -> str:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["agent_id"]
    agent_id = str(uuid.uuid4())
    CONFIG_PATH.write_text(json.dumps({"agent_id": agent_id}, indent=2), encoding="utf-8")
    return agent_id

def get_network_context_windows():
    ps = r"""
    $cfg = Get-NetIPConfiguration |
      Where-Object { $_.IPv4Address -ne $null -and $_.NetProfile -ne $null } |
      Select-Object InterfaceAlias,
                    @{n='IPv4';e={$_.IPv4Address.IPAddress}},
                    @{n='PrefixLength';e={$_.IPv4Address.PrefixLength}},
                    @{n='Gateway';e={ if ($_.IPv4DefaultGateway) { $_.IPv4DefaultGateway.NextHop } else { $null } }},
                    @{n='InterfaceMetric';e={$_.NetIPv4Interface.InterfaceMetric}} |
      ConvertTo-Json -Depth 3
    $cfg
    """
    out = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", ps],
        text=True, encoding="utf-8", errors="ignore"
    ).strip()
    data = json.loads(out)
    items = [data] if isinstance(data, dict) else data

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
        candidates.append((score, ipv4, gw or "", str(network)))

    if not candidates:
        raise RuntimeError("Could not detect network context")

    candidates.sort(reverse=True, key=lambda x: x[0])
    _, local_ip, gateway_ip, cidr = candidates[0]
    return local_ip, gateway_ip, cidr

def run_once():
    agent_id = load_or_create_agent_id()
    local_ip, gateway_ip, cidr = get_network_context_windows()

    devices = scan_by_arp(cidr, local_ip=local_ip, timeout=2)

    classified = classify_devices(
        devices,
        oui_csv_path="files/oui.csv",
        gateway_ip=gateway_ip
    )

    payload = {
        "agent_id": agent_id,
        "network": {
            "cidr": cidr,
            "gateway": gateway_ip,
            "local_ip": local_ip
        },
        "devices": classified
    }
    r = requests.post(
        SERVER_URL,
        json=payload,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=15,
    )

    print("Server response:", r.status_code, r.text)
    return r.status_code

def main():
    # כל 5 דקות (תשנה)
    while True:
        try:
            status = run_once()
            print("Reported to server:", status)
        except Exception as e:
            print("Agent error:", e)
        time.sleep(300)
        
if __name__ == "__main__":
    main()
    #run_once()