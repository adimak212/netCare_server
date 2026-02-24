from scapy.all import ARP, Ether, srp, get_if_list, get_if_addr
import ipaddress


def pick_iface_by_ip(local_ip: str) -> str:
    for iface in get_if_list():
        try:
            if get_if_addr(iface) == local_ip:
                return iface
        except Exception:
            pass
    raise ValueError(f"No interface found with IP {local_ip}")
import socket

def get_local_ip_for_network(cidr):
    network = ipaddress.ip_network(cidr, strict=False)
    target_ip = str(list(network.hosts())[0])

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target_ip, 1))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    return local_ip

def scan_by_arp(cidr: str, local_ip: str, timeout: int = 2):
    ipaddress.ip_network(cidr, strict=False)
    

    
    local_ip = get_local_ip_for_network(cidr)
    print("ip : " , local_ip)
    iface = pick_iface_by_ip(local_ip)

    arp = ARP(pdst=cidr)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    answered, _ = srp(packet, timeout=timeout, verbose=False, iface=iface)

    devices = [{"ip": recv.psrc, "mac": recv.hwsrc} for _, recv in answered]
    devices.sort(key=lambda d: tuple(int(x) for x in d["ip"].split(".")))
    return devices
