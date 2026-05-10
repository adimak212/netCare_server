import asyncio
import re
import telnetlib3
import ipaddress


class NetCareScanner:
    def __init__(self, username, password, network_cidr):
        self.username = username
        self.password = password

        self.visited = set()
        self.devices = {}
        self.neighbors = []
        self.arp_table = {}          # ip -> clean_mac
        self.switch_mac_tables = {}  # sw_ip -> { clean_mac -> port }

        try:
            self.network = ipaddress.ip_network(network_cidr, strict=False)
        except Exception:
            self.network = None

    # ------------------------------------------------------------------ helpers

    def is_valid_ip(self, ip):
        try:
            return ipaddress.ip_address(ip) in self.network if self.network else True
        except Exception:
            return False

    def clean_mac(self, mac):
        """Normalise any MAC format to 12 lowercase hex chars."""
        return re.sub(r'[^0-9a-fA-F]', '', mac).lower()

    # ------------------------------------------------------------------ telnet

    async def connect(self, host):
        return await telnetlib3.open_connection(host, 23)

    async def send(self, writer, cmd):
        writer.write(cmd + "\n")
        await writer.drain()
        await asyncio.sleep(0.4)

    async def read(self, reader, timeout=1.2):
        data = ""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=timeout)
                if not chunk:
                    break
                data += chunk
        except Exception:
            pass
        return data

    # ------------------------------------------------------------------ ping sweep

    async def ping_sweep(self, writer, reader, host):
        """
        שולח ping לכל ה-IPs הידועים מה-ARP table (לא כולל את המכשיר עצמו).
        זה גורם לסוויץ' לאכלס את ה-MAC table שלו לפני שאנחנו קוראים אותו.
        """
        known_ips = list(self.arp_table.keys())

        if not known_ips:
            return

        for ip_str in known_ips:
            if ip_str != host:
                writer.write(f"ping {ip_str} repeat 1 timeout 1\n")
                await writer.drain()
                await asyncio.sleep(0.05)

        # ממתינים שכל ה-pings יסתיימו ומרוקנים את ה-buffer
        await asyncio.sleep(2.0)
        await self.read(reader, timeout=3.0)

    # ------------------------------------------------------------------ scan

    async def scan_device(self, host, name="Unknown"):
        if host in self.visited or not self.is_valid_ip(host):
            return

        self.visited.add(host)

        if host not in self.devices:
            self.devices[host] = {"ip": host, "name": name, "is_pc": False}

        try:
            reader, writer = await self.connect(host)

            await self.send(writer, self.username)
            await self.send(writer, self.password)
            await self.send(writer, "terminal length 0")
            await self.read(reader)

            # ── CDP ──────────────────────────────────────────────────────────
            await self.send(writer, "show cdp neighbors detail")
            cdp = await self.read(reader)

            for block in cdp.split("Device ID:")[1:]:
                try:
                    neighbor_name = block.strip().split("\n")[0].strip()
                    ip_m    = re.search(r"IP address: (\S+)", block)
                    iface_m = re.search(r"Interface: (.*?),", block)
                    port_m  = re.search(r"Port ID \(outgoing port\): (.*)", block)

                    if ip_m and iface_m and port_m:
                        nip = ip_m.group(1)
                        if self.is_valid_ip(nip):
                            if nip not in self.devices:
                                self.devices[nip] = {
                                    "ip": nip,
                                    "name": neighbor_name,
                                    "is_pc": False,
                                }
                            self.neighbors.append({
                                "src":      host,
                                "dst":      nip,
                                "src_port": iface_m.group(1).strip(),
                                "dst_port": port_m.group(1).strip(),
                            })
                            await self.scan_device(nip, neighbor_name)
                except Exception:
                    continue

            # ── ARP ──────────────────────────────────────────────────────────
            await self.send(writer, "show ip arp")
            arp = await self.read(reader)

            for m in re.finditer(
                r"(\d+\.\d+\.\d+\.\d+)\s+\S+\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}"
                r"|[0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}[:\-]"
                r"[0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2})\s+ARPA",
                arp
            ):
                ip_addr, mac_raw = m.group(1), m.group(2)
                if self.is_valid_ip(ip_addr):
                    self.arp_table[ip_addr] = self.clean_mac(mac_raw)

            # ── PING SWEEP (לפני MAC table) ──────────────────────────────────
            # מפנג את כל ה-IPs הידועים כדי שה-switch יאכלס את ה-MAC table שלו
            await self.ping_sweep(writer, reader, host)

            # ── MAC TABLE ────────────────────────────────────────────────────
            await self.send(writer, "show mac address-table")
            mac_raw_out = await self.read(reader, timeout=2.0)

            entries = re.findall(
                r"\d+\s+([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})\s+DYNAMIC\s+(\S+)",
                mac_raw_out
            )
            if entries:
                self.switch_mac_tables[host] = {
                    self.clean_mac(mac): port for mac, port in entries
                }

            writer.close()

        except Exception:
            pass

    # ------------------------------------------------------------------ finalize

    def finalize_pcs(self):
        """
        זיהוי PCs בשתי שיטות משלימות:

        שיטה א' – מה-ARP של ה-router (אמינה תמיד):
          כל IP ב-ARP שאינו מכשיר תשתית ידוע = PC.
          מנסה למצוא את פרטי החיבור (switch + port) מה-MAC tables.

        שיטה ב' – מה-MAC tables של הסוויצ'ים (רק MACs שיש להם IP ב-ARP):
          עבור כל MAC ב-MAC table שיש לו IP ב-ARP וה-IP אינו תשתית → PC.
          זה מכסה מקרים שה-router לא ראה ב-ARP.
        """

        infra_ips:  set[str] = set(
            ip for ip, d in self.devices.items() if not d.get("is_pc")
        )
        infra_macs: set[str] = set(
            mac for ip, mac in self.arp_table.items() if ip in infra_ips
        )

        mac_to_ip: dict[str, str] = {mac: ip for ip, mac in self.arp_table.items()}

        # ── שיטה א': כל IP ב-ARP שאינו תשתית ──────────────────────────────
        pc_ips_from_arp: set[str] = set(
            ip for ip in self.arp_table if ip not in infra_ips
        )

        for pc_ip in pc_ips_from_arp:
            pc_mac = self.arp_table[pc_ip]

            parent_switch = None
            parent_port   = None

            for sw_ip, mac_table in self.switch_mac_tables.items():
                if pc_mac in mac_table:
                    parent_switch = sw_ip
                    parent_port   = mac_table[pc_mac]
                    break

            self.devices[pc_ip] = {
                "ip":            pc_ip,
                "name":          f"PC_{pc_ip.split('.')[-1]}",
                "is_pc":         True,
                "mac":           pc_mac,
                "parent_switch": parent_switch,
                "port":          parent_port,
            }

        # ── שיטה ב': MAC table entries עם IP ידוע שאינם תשתית ──────────────
        for sw_ip, mac_table in self.switch_mac_tables.items():
            for mac, port in mac_table.items():

                if mac in infra_macs:
                    continue

                ip_match = mac_to_ip.get(mac)
                if not ip_match or ip_match in infra_ips:
                    continue

                existing = self.devices.get(ip_match)
                if existing and existing.get("parent_switch"):
                    continue

                self.devices[ip_match] = {
                    "ip":            ip_match,
                    "name":          f"PC_{ip_match.split('.')[-1]}",
                    "is_pc":         True,
                    "mac":           mac,
                    "parent_switch": sw_ip,
                    "port":          port,
                }

    # ------------------------------------------------------------------ props

    @property
    def devices_list(self):
        return list(self.devices.values())

    @property
    def links_list(self):
        return self.neighbors