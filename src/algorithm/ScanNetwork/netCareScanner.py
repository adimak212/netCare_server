import asyncio
import re
import json
import telnetlib3
import ipaddress

class NetCareScanner:
    def __init__(self, username, password, network_cidr):
        self.username = username
        self.password = password
        self.visited_ips = set()
        self.infra_ips = set()
        self.all_arp_entries = {}
        self.devices_list = []
        self.links_list = []
        try:
            self.network = ipaddress.ip_network(network_cidr, strict=False)
        except:
            raise

    def is_in_network(self, ip_str):
        try:
            return ipaddress.ip_address(ip_str) in self.network
        except:
            return False

    async def capture_output(self, reader):
        full_output = ""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=1.5)
                if not chunk:
                    break
                full_output += chunk
        except asyncio.TimeoutError:
            pass
        return full_output

    def is_pc_mac(self, mac_addr):
        return mac_addr.lower().startswith("0050.79")

    def add_link(self, source, target, s_port, t_port):
        for link in self.links_list:
            if (link["source"] == source and link["target"] == target) or \
               (link["source"] == target and link["target"] == source):
                return
        self.links_list.append({
            "source": source,
            "target": target,
            "source_port": s_port,
            "target_port": t_port
        })

    def determine_node_type(self, name, capabilities_str):
        """
        מסווג מכשיר לפי מחרוזת ה-Capabilities שהתקבלה מה-CDP של השכן.
        כך נמנע מלקרוא capabilities של שכנים אחרים ולטעות בסיווג.
        """
        cap_lower = capabilities_str.lower()

        # עדיפות לסוויץ': אם מופיעה המילה switch בכל צורה
        if 'switch' in cap_lower:
            return "cisco_switch", "switch.png"

        # ראוטר טהור: רק router ללא switch
        if 'router' in cap_lower:
            return "dynamips", "router.png"

        # גיבוי לפי שם המכשיר אם CDP לא סיפק מידע
        name_lower = name.lower()
        if "esw" in name_lower or "switch" in name_lower:
            return "cisco_switch", "switch.png"

        return "dynamips", "router.png"

    async def scan_device(self, host, device_name="Unknown", capabilities_str=""):
        """
        סורק מכשיר בודד באמצעות Telnet.
        capabilities_str מגיע מה-CDP block של המכשיר שגילה אותנו,
        ולכן מתאר אותנו בלבד — ולא את שכנינו.
        """
        if not self.is_in_network(host) or host in self.visited_ips:
            return

        print(f"[NetCare] >>> Scanning Infrastructure: {device_name} ({host})")
        self.visited_ips.add(host)
        self.infra_ips.add(host)

        try:
            reader, writer = await asyncio.wait_for(
                telnetlib3.open_connection(host, 23), timeout=5.0
            )

            async def send_cmd(cmd):
                writer.write(cmd + '\r\n')
                await writer.drain()
                await asyncio.sleep(0.8)

            await send_cmd(self.username)
            await send_cmd(self.password)
            await send_cmd('terminal length 0')
            await self.capture_output(reader)

            # --- CDP ---
            await send_cmd('show cdp neighbors detail')
            cdp_raw = await self.capture_output(reader)

            infra_found = []
            for block in cdp_raw.split('-------------------------'):
                n_ip      = re.search(r'IP address: (\d{1,3}(?:\.\d{1,3}){3})', block)
                n_name    = re.search(r'Device ID: (.*?)\s', block)
                n_cap     = re.search(r'Capabilities:\s+(.*)', block, re.IGNORECASE)
                port_info = re.search(
                    r'Interface: (.*?),.*?Port ID \(outgoing port\): (.*?)\s',
                    block, re.DOTALL
                )

                if n_ip and n_name and port_info:
                    nip = n_ip.group(1)
                    neighbor_caps = n_cap.group(1).strip() if n_cap else ""

                    if self.is_in_network(nip):
                        self.infra_ips.add(nip)
                        self.add_link(
                            host, nip,
                            port_info.group(1).strip(),
                            port_info.group(2).strip()
                        )
                        if nip not in self.visited_ips:
                            infra_found.append({
                                "ip":           nip,
                                "name":         n_name.group(1).strip(),
                                "capabilities": neighbor_caps   # ← capabilities של השכן בלבד
                            })

            # --- ARP ---
            await send_cmd('show ip arp')
            arp_raw = await self.capture_output(reader)
            matches = re.findall(
                r'(\d{1,3}(?:\.\d{1,3}){3})\s+.*?\s+.*?\s+.*?\s+(\S+)', arp_raw
            )
            for ip, interface in matches:
                if self.is_in_network(ip) and ip != host:
                    self.all_arp_entries[ip] = {"parent": host, "interface": interface}

            # סיווג המכשיר הנוכחי לפי ה-capabilities שהתקבלו מהשכן שגילה אותנו
            node_type, icon = self.determine_node_type(device_name, capabilities_str)
            self.devices_list.append({
                "node_id":   host,
                "name":      device_name,
                "modelType": "Cisco",
                "node_type": node_type,
                "icon":      icon,
                "x":         0,
                "y":         0,
                "ports":     [],
                "console":   23
            })

            writer.close()

            # סריקה רקורסיבית — כל שכן מקבל את ה-capabilities שלו בלבד
            for neighbor in infra_found:
                await self.scan_device(
                    neighbor["ip"],
                    neighbor["name"],
                    neighbor["capabilities"]
                )

        except Exception as e:
            print(f"  [X] Error on {host}: {e}")

    def finalize_pcs(self):
        """מוסיף PCs שהתגלו ב-ARP אך אינם חלק מהתשתית."""
        for ip, info in self.all_arp_entries.items():
            if ip not in self.infra_ips:
                self.devices_list.append({
                    "node_id":   ip,
                    "name":      f"PC_{ip.split('.')[-1]}",
                    "modelType": "Generic PC",
                    "node_type": "vpcs",
                    "icon":      "vpcs.png",
                    "x":         0,
                    "y":         0,
                    "ports":     [],
                    "console":   0
                })
                self.infra_ips.add(ip)
                self.add_link(info["parent"], ip, info["interface"], "eth0")

    def save_to_json(self):
        self.finalize_pcs()
        output = {"nodes": self.devices_list, "links": self.links_list}
        with open("topology_data.json", "w") as f:
            json.dump(output, f, indent=4)
        print(f"\n[NetCare] Scan Complete. Saved to topology_data.json")