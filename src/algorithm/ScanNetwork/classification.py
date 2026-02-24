from __future__ import annotations

import csv
import socket
from typing import Dict, List, Optional, Tuple

COMMON_PORTS: Dict[int, str] = {
    22: "ssh",
    53: "dns-tcp",
    80: "http",
    443: "https",
    161: "snmp",
    445: "smb",
    3389: "rdp",
    631: "ipp",
    9100: "jetdirect",
    554: "rtsp",
    8080: "http-8080",
    8443: "https-8443",
}

NETWORK_VENDOR_KEYWORDS = (
    "ruckus",
    "ubiquiti",
    "check point",
    "cisco",
    "juniper",
    "aruba",
    "hpe",
    "hp",
    "mikrotik",
    "tp-link",
    "d-link",
    "netgear",
    "fortinet",
    "palo alto",
    "watchguard",
    "sonicwall",
    "meraki",
    "extreme",
    "huawei",
)

def load_oui_csv(path: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignment = (row.get("Assignment") or "").strip().replace("-", "").replace(":", "").upper()
            org = (row.get("Organization Name") or "").strip()
            if len(assignment) == 6 and org:
                mapping[assignment] = org
    return mapping

def mac_to_vendor(mac: str, oui_map: Optional[Dict[str, str]]) -> str:
    if not oui_map:
        return "Unknown"
    prefix = mac.replace(":", "").replace("-", "").upper()[:6]
    return oui_map.get(prefix, "Unknown")

def check_open_services(ip: str, timeout: float = 0.30, ports: Dict[int, str] = COMMON_PORTS) -> List[str]:
    services: List[str] = []
    for port, name in ports.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            services.append(name)
        except Exception:
            pass
        finally:
            s.close()
    return services

def is_network_vendor(vendor: str) -> bool:
    v = vendor.lower()
    return any(k in v for k in NETWORK_VENDOR_KEYWORDS)

def categorize(vendor: str, services: List[str], is_gateway: bool = False) -> Tuple[str, int]:
    sv = set(services)

    if is_gateway:
        conf = 95
        if is_network_vendor(vendor):
            conf = 99
        return ("NETWORK_DEVICE", conf)

    if is_network_vendor(vendor):
        conf = 85
        if sv.intersection({"snmp", "ssh", "http", "https", "http-8080", "https-8443"}):
            conf = 95
        return ("NETWORK_DEVICE", conf)

    if sv.intersection({"snmp", "ssh"}):
        return ("NETWORK_DEVICE", 80)

    if sv.intersection({"smb", "rdp"}):
        return ("HOST", 85)

    if sv.intersection({"ipp", "jetdirect", "rtsp"}):
        return ("HOST", 75)

    if sv.intersection({"http", "https", "http-8080", "https-8443"}):
        return ("HOST", 55)

    if vendor != "Unknown":
        return ("HOST", 45)

    return ("UNKNOWN", 25)

def classify_devices(
    devices: List[dict],
    oui_csv_path: Optional[str] = None,
    port_timeout: float = 0.30,
    gateway_ip: Optional[str] = None,
) -> List[dict]:
    oui_map = load_oui_csv(oui_csv_path) if oui_csv_path else None
    results: List[dict] = []

    for d in devices:
        ip = d["ip"]
        mac = d["mac"]

        vendor = mac_to_vendor(mac, oui_map)
        services = check_open_services(ip, timeout=port_timeout)
        category, conf = categorize(vendor, services, is_gateway=(gateway_ip is not None and ip == gateway_ip))

        results.append({
            "ip": ip,
            "mac": mac,
            "vendor": vendor,
            "services": services,
            "category": category,
            "confidence": conf,
        })

    def ip_key(x: str):
        return tuple(int(p) for p in x.split("."))

    results.sort(key=lambda r: ip_key(r["ip"]))
    return results

def filter_network_devices(classified: List[dict], min_confidence: int = 70) -> List[dict]:
    return [d for d in classified if d["category"] == "NETWORK_DEVICE" and d["confidence"] >= min_confidence]


def role_from_snmp(snmp_info: Dict[str, str], vendor: str = "") -> Tuple[str, int]:
    text = (snmp_info.get("sysDescr", "") + " " + snmp_info.get("sysName", "")).lower()
    v = vendor.lower()

    firewall_keys = ("check point", "fortinet", "palo alto", "sonicwall", "watchguard")
    switch_keys = ("switch", "catalyst", "procurve", "arubaos-switch", "nx-os", "ios xe", "extreme", "brocade")
    router_keys = ("router", "routeros", "edgeos", "vyos", "ios xr")
    ap_keys = ("ruckus", "unifi ap", "access point", "aruba ap", "aironet", "zoneflex")

    if any(k in text for k in firewall_keys) or any(k in v for k in firewall_keys):
        return ("FIREWALL", 98)

    if "gateway" in text and (any(k in text for k in firewall_keys) or "check point" in v):
        return ("FIREWALL", 98)

    if any(k in text for k in switch_keys):
        return ("SWITCH", 96)

    if any(k in text for k in router_keys):
        return ("ROUTER", 96)

    if any(k in text for k in ap_keys):
        return ("ACCESS_POINT", 96)

    if "ubiquiti" in v and ("unifi" in text or "uap" in text):
        return ("ACCESS_POINT", 96)

    return ("NETWORK_DEVICE", 90)