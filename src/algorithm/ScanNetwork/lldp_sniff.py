import binascii
from scapy.all import sniff, Ether, Raw, conf

LLDP_ETHERTYPE = 0x88CC

def _mac_from_oid_tail(tail_bytes: bytes) -> str:
    # לפעמים MAC מופיע כ-6 בתים בתוך TLV
    if len(tail_bytes) >= 6:
        b = tail_bytes[:6]
        return ":".join(f"{x:02x}" for x in b)
    return ""

def parse_lldp_tlvs(payload: bytes):
    """
    LLDP payload הוא רצף TLV:
    - header: 2 bytes => type(7 bits) + length(9 bits)
    - value: length bytes
    type=0 => End of LLDPDU
    """
    i = 0
    info = {}
    while i + 2 <= len(payload):
        hdr = int.from_bytes(payload[i:i+2], "big")
        tlv_type = (hdr >> 9) & 0x7F
        tlv_len = hdr & 0x1FF
        i += 2
        if i + tlv_len > len(payload):
            break
        val = payload[i:i+tlv_len]
        i += tlv_len

        if tlv_type == 0:  # End
            break

        # 1 = Chassis ID, 2 = Port ID, 5 = System Name, 6 = System Description
        if tlv_type == 1 and tlv_len >= 2:
            # val[0] = subtype
            info["chassis_subtype"] = val[0]
            info["chassis_id_raw"] = val[1:]
        elif tlv_type == 2 and tlv_len >= 2:
            info["port_subtype"] = val[0]
            info["port_id_raw"] = val[1:]
        elif tlv_type == 5:
            info["system_name"] = val.decode("utf-8", errors="ignore").strip("\x00")
        elif tlv_type == 6:
            info["system_descr"] = val.decode("utf-8", errors="ignore").strip("\x00")

    # ניסיון להמיר chassis/port ל-string
    if "chassis_id_raw" in info:
        # subtype 4 בדרך כלל MAC address
        if info.get("chassis_subtype") == 4:
            info["chassis_mac"] = ":".join(f"{b:02x}" for b in info["chassis_id_raw"][:6])
        else:
            info["chassis_id"] = info["chassis_id_raw"].decode("utf-8", errors="ignore")

    if "port_id_raw" in info:
        # subtype 3=MAC, 5=ifName, 7=local
        if info.get("port_subtype") == 3:
            info["port_mac"] = ":".join(f"{b:02x}" for b in info["port_id_raw"][:6])
        else:
            info["port_id"] = info["port_id_raw"].decode("utf-8", errors="ignore")

    return info

def on_pkt(pkt):
    if not pkt.haslayer(Ether):
        return
    eth = pkt[Ether]
    if eth.type != LLDP_ETHERTYPE:
        return

    payload = bytes(pkt[Raw].load) if pkt.haslayer(Raw) else b""
    info = parse_lldp_tlvs(payload)

    print("\n=== LLDP Neighbor ===")
    print("Src MAC:", eth.src)
    if info.get("system_name"):
        print("System Name:", info["system_name"])
    if info.get("chassis_mac"):
        print("Chassis MAC:", info["chassis_mac"])
    if info.get("port_id"):
        print("Port ID:", info["port_id"])
    if info.get("system_descr"):
        print("Descr:", info["system_descr"][:120])

def main():
    print("Listening for LLDP (EtherType 0x88cc) ...")
    # אם יש לך כמה כרטיסי רשת, אפשר להגדיר iface=...
    sniff(prn=on_pkt, store=False, filter="ether proto 0x88cc", timeout=60)

if __name__ == "__main__":
    main()