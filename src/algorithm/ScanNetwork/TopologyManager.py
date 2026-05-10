import uuid
import re


class TopologyManager:

    @staticmethod
    def parse_port(port_str: str) -> dict:
        """
        Convert a Cisco interface name into GNS3/EVE-NG adapter + port numbers.

        Examples
        --------
        GigabitEthernet0/0  -> adapter=0, port=0
        GigabitEthernet0/1  -> adapter=0, port=1
        GigabitEthernet1/0  -> adapter=1, port=0
        Gi0/2               -> adapter=0, port=2
        FastEthernet0/1     -> adapter=0, port=1
        Ethernet0           -> adapter=0, port=0
        Fa1/0/3             -> adapter=1, port=3   (3-level: slot/module/port)
        """
        # Try slot/subslot/port  (e.g. GigabitEthernet1/0/3)
        m = re.search(r"(\d+)/(\d+)/(\d+)", port_str)
        if m:
            return {"adapter_number": int(m.group(1)), "port_number": int(m.group(3))}

        # Try slot/port  (e.g. GigabitEthernet0/1)
        m = re.search(r"(\d+)/(\d+)", port_str)
        if m:
            return {"adapter_number": int(m.group(1)), "port_number": int(m.group(2))}

        # Try single number  (e.g. Ethernet0)
        m = re.search(r"(\d+)", port_str)
        if m:
            return {"adapter_number": 0, "port_number": int(m.group(1))}

        return {"adapter_number": 0, "port_number": 0}

    @staticmethod
    def create_final_topology(devices, neighbors, mac_tables=None):
        nodes = []
        links = []

        # ── Nodes ─────────────────────────────────────────────────────────────
        for d in devices:
            name = d.get("name", "")

            if d.get("is_pc"):
                node_type = "vpcs"
            elif "router" in name.lower() or "core" in name.lower():
                node_type = "dynamips"
            else:
                node_type = "ethernet_switch"

            nodes.append({
                "node_id":   d["ip"],
                "name":      name,
                "node_type": node_type,
                "x": d.get("x", 0),
                "y": d.get("y", 0),
                "status":    "stopped",
            })

        # ── CDP links (infrastructure ↔ infrastructure) ───────────────────────
        for n in neighbors:
            src_port = TopologyManager.parse_port(n["src_port"])
            dst_port = TopologyManager.parse_port(n["dst_port"])

            links.append({
                "link_id": str(uuid.uuid4()),
                "from": {
                    "node_id":        n["src"],
                    "adapter_number": src_port["adapter_number"],
                    "port_number":    src_port["port_number"],
                },
                "to": {
                    "node_id":        n["dst"],
                    "adapter_number": dst_port["adapter_number"],
                    "port_number":    dst_port["port_number"],
                },
            })

        # ── PC links (switch ↔ PC) ────────────────────────────────────────────
        # Track which switch ports are already used by CDP links so we don't
        # assign the same port to two different connections.
        used_switch_ports: dict[str, set] = {}   # sw_ip -> {port_number, ...}

        for lnk in links:
            for side in ("from", "to"):
                nid = lnk[side]["node_id"]
                pn  = lnk[side]["port_number"]
                used_switch_ports.setdefault(nid, set()).add(pn)

        for d in devices:
            if not d.get("is_pc"):
                continue

            parent = d.get("parent_switch")
            port   = d.get("port", "Gi0/0")

            if not parent:
                continue

            sw_port = TopologyManager.parse_port(port)

            # If the exact port is already used by a CDP link, pick the next
            # available port on that switch to avoid collisions.
            occupied = used_switch_ports.get(parent, set())
            pn = sw_port["port_number"]
            while pn in occupied:
                pn += 1
            used_switch_ports.setdefault(parent, set()).add(pn)

            links.append({
                "link_id": str(uuid.uuid4()),
                "from": {
                    "node_id":        parent,
                    "adapter_number": sw_port["adapter_number"],
                    "port_number":    pn,
                },
                "to": {
                    # PCs (VPCS) always use adapter 0, port 0
                    "node_id":        d["ip"],
                    "adapter_number": 0,
                    "port_number":    0,
                },
            })

        return nodes, links

    @staticmethod
    def apply_force_layout(devices, links):
        """
        Simple grid layout.  Separates infrastructure nodes from PCs so the
        diagram is easier to read:

          Row 0:  routers / firewalls
          Row 1:  switches
          Row 2+: PCs
        """
        routers  = [d for d in devices if "router" in d.get("name","").lower()
                                       or "core"   in d.get("name","").lower()]
        switches = [d for d in devices if not d.get("is_pc")
                                       and d not in routers]
        pcs      = [d for d in devices if d.get("is_pc")]

        def place_row(group, y, x_start=0, gap=200):
            for i, node in enumerate(group):
                node["x"] = x_start + i * gap
                node["y"] = y

        place_row(routers,  y=0,   gap=250)
        place_row(switches, y=200, gap=250)
        place_row(pcs,      y=400, gap=180)