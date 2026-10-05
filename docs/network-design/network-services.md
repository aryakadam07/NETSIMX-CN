# NETSIMX — Network Services Documentation

**Document ID:** NX-DES-007  
**Author:** Member 1 (Network Architecture, Addressing & Cisco Packet Tracer)  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Branch:** `arya`  
**Status:** Approved Baseline  

---

## 1. Overview of Network Services

NETSIMX provides three essential enterprise network services:
1. **Dynamic Host Configuration Protocol (DHCP):** Automatic IPv4 address, subnet mask, default gateway, and DNS server assignment for workstations.
2. **Domain Name System (DNS):** Hostname resolution mapping human-readable URLs (`netsimx.local`) to server IP addresses.
3. **Hypertext Transfer Protocol (HTTP Web Service):** Enterprise Web Portal hosting live system status, telemetry reports, and documentation.

---

## 2. Service 1 — Dynamic Host Configuration Protocol (DHCP)

### Service Architecture
* **Provider Device:** Edge Router `R1`
* **Target Subnet:** Workstation LAN (`192.168.1.0/24`)
* **Pool Name:** `LAN_WORKSTATIONS`

### Configuration Details
* **Network Scope:** `192.168.1.0 255.255.255.0`
* **Excluded Addresses:** `192.168.1.1` to `192.168.1.49` (reserved for router gateways, management SVIs, and static hosts).
* **Lease Pool Range:** `192.168.1.50` to `192.168.1.150`
* **Default Router (Gateway):** `192.168.1.1`
* **DNS Server:** `172.16.1.10`
* **Domain Name:** `netsimx.local`

### Client Access Procedure
1. Workstations (`PC1`, `PC2`) set IP Configuration to **DHCP** in operating system properties.
2. PC broadcasts a `DHCPDISCOVER` message on `VLAN 10`.
3. Router `R1` intercepts the request and responds with `DHCPOFFER` offering IP `192.168.1.50`, GW `192.168.1.1`, DNS `172.16.1.10`.
4. PC sends `DHCPREQUEST`, and `R1` returns `DHCPACK` confirming lease.

---

## 3. Service 2 — Domain Name System (DNS)

### Service Architecture
* **Provider Device:** `DNS-Server`
* **IP Address:** `172.16.1.10/24`
* **Default Gateway:** `172.16.1.1`

### Resource Records
| Domain Name (FQDN) | Record Type | Target IP Address | Purpose |
|---|---|---|---|
| `netsimx.local` | A Record | `172.16.1.100` | NetSimX Web Portal |
| `www.netsimx.local` | CNAME | `netsimx.local` | Web Alias |
| `dns.netsimx.local` | A Record | `172.16.1.10` | DNS Server Self-Reference |

### Client Access Procedure
1. Client workstation opens web browser and enters `http://netsimx.local`.
2. Client queries DNS Server at `172.16.1.10` via UDP port 53.
3. DNS Server looks up A Record and returns `172.16.1.100`.
4. Client initiates HTTP connection to `172.16.1.100`.

---

## 4. Service 3 — HTTP Web Service (Enterprise Web Portal)

### Service Architecture
* **Provider Device:** `Server1` (Web Server)
* **IP Address:** `172.16.1.100/24`
* **Default Gateway:** `172.16.1.1`
* **Port:** TCP Port 80 (HTTP)

### Web Portal Content (`index.html`)
```html
<!DOCTYPE html>
<html>
<head>
    <title>NetSimX — Intelligent Network Platform</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0b0f19; color: #e2e8f0; margin: 40px; }
        h1 { color: #38bdf8; }
        .card { background: #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .status { color: #4ade80; font-weight: bold; }
    </style>
</head>
<body>
    <h1>NetSimX System Portal</h1>
    <div class="card">
        <h2>Network Status: <span class="status">OPERATIONAL</span></h2>
        <p><strong>Primary Route:</strong> PC1 -> R1 -> R2 -> R4 -> Server1 (Cost: 6.0)</p>
        <p><strong>Backup Route:</strong> PC1 -> R1 -> R3 -> R4 -> Server1 (Cost: 10.0)</p>
        <p><strong>Routing Protocol:</strong> OSPF Area 0 (Link-State / Dijkstra)</p>
    </div>
</body>
</html>
```

### Client Verification Procedure
* In Cisco Packet Tracer, open **PC1** $\rightarrow$ **Desktop** $\rightarrow$ **Web Browser**.
* Enter `http://172.16.1.100` or `http://netsimx.local`.
* Verify that the NetSimX System Portal page renders cleanly.
