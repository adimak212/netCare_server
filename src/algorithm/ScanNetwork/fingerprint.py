import socket
import ssl


HTTP_PORTS = (80, 443, 8080, 8443)


def http_fingerprint(ip: str, timeout: float = 2.0) -> str | None:
    for port in HTTP_PORTS:
        try:
            sock = socket.create_connection((ip, port), timeout=timeout)

            # HTTPS handling בלי אימות תעודה
            if port in (443, 8443):
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock)

            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {ip}\r\n"
                f"User-Agent: Mozilla/5.0\r\n"
                f"Connection: close\r\n\r\n"
            )

            sock.send(request.encode())
            data = sock.recv(8192).decode(errors="ignore")
            sock.close()

            if data:
                return data.lower()

        except Exception:
            continue

    return None


def ssh_banner(ip: str, timeout: float = 2.0) -> str | None:
    try:
        sock = socket.create_connection((ip, 22), timeout=timeout)
        banner = sock.recv(1024).decode(errors="ignore")
        sock.close()
        return banner.lower()
    except Exception:
        return None


def classify_from_fingerprint(
    ip: str,
    vendor: str,
    is_gateway: bool = False
) -> str | None:

    http_data = http_fingerprint(ip)
    ssh_data = ssh_banner(ip)

    text = ""
    if http_data:
        text += http_data
    if ssh_data:
        text += ssh_data

    v = vendor.lower()

    # 🎯 אם זה ה-gateway – סביר מאוד שזה ROUTER
    if is_gateway:
        return "ROUTER"

    # 🔥 Firewall vendors
    if any(x in v for x in ("check point", "fortinet", "palo alto",
                            "sonicwall", "watchguard")):
        return "FIREWALL"

    if any(x in text for x in ("firewall", "utm", "vpn gateway")):
        return "FIREWALL"

    # 📡 Access Points
    if any(x in v for x in ("ruckus", "ubiquiti", "aruba")):
        return "ACCESS_POINT"

    if any(x in text for x in ("unifi", "access point", "zoneflex", "aironet")):
        return "ACCESS_POINT"

    # 🔀 Switch
    if any(x in text for x in ("cisco ios", "catalyst", "nx-os",
                               "procurve", "arubaos-switch")):
        return "SWITCH"

    # 🛜 Router / CPE vendors
    if any(x in v for x in (
        "vantiva",
        "technicolor",
        "sercomm",
        "arcadyan",
        "sagemcom",
        "commscope",
        "zte",
        "huawei",
        "tp-link",
        "d-link",
        "netgear",
        "mikrotik",
    )):
        return "ROUTER"

    if any(x in text for x in ("routeros", "edgeos", "openwrt", "dd-wrt")):
        return "ROUTER"

    return None
