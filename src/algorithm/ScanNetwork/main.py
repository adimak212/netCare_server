from scan import scan_by_arp
from classification import classify_devices, filter_network_devices
from snmp import snmp_basic_info
from fingerprint import classify_from_fingerprint

CIDR = "192.168.1.0/24"
LOCAL_IP = "192.168.1.106"
GATEWAY_IP = "192.168.1.1"

def main():
    print("🔎 Running ARP scan...")
    devices = scan_by_arp(CIDR, local_ip=LOCAL_IP, timeout=2)


    print(f"Found {len(devices)} devices\n")

    classified = classify_devices(
        devices,
        oui_csv_path="files/oui.csv",
        gateway_ip=GATEWAY_IP
    )

    for d in classified:
        ip = d["ip"]
        vendor = d["vendor"]
        
        snmp_info = snmp_basic_info(ip)
        if snmp_info:
            print("SNMP ENABLED")
            print("sysName:", snmp_info["sysName"])
        else:
            #print("No SNMP response")
            pass

        print(f"\nDevice: {ip}")
        print("Vendor:", vendor)
        print("Category:", d["category"], "Confidence:", d["confidence"])

        # SNMP check
        snmp_info = snmp_basic_info(ip)
        if snmp_info:
            print("SNMP sysName:", snmp_info["sysName"])
            print("SNMP sysDescr:", snmp_info["sysDescr"][:100])

        # Fingerprint role
        role = classify_from_fingerprint(ip, vendor, is_gateway=(ip == GATEWAY_IP))
        if role:
            print("Role:", role)


if __name__ == "__main__":
    main()
