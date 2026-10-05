# NETSIMX — IP Addressing & Subnetting Plan

**Document ID:** NX-DES-003  
**Author:** Member 1 (Network Architecture, Addressing & Cisco Packet Tracer)  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Branch:** `arya`  
**Status:** Approved Baseline  

---

## 1. Executive Summary & Subnet Strategy

The IP addressing plan for NETSIMX uses Variable Length Subnet Masking (VLSM) under standard IPv4 Class A, B, and C private address space (RFC 1918). 
* **User LAN Subnet (`/24`):** Allocates up to 254 hosts for client workstations and local services.
* **Server DMZ Subnet (`/24`):** Reserves static addresses for enterprise servers, DNS, and web portals.
* **Core Point-to-Point Links (`/30`):** Maximizes address efficiency for 2-host inter-router links, minimizing wasted space.

---

## 2. Complete IP Addressing Table

| Device Name | Interface | Subnet Network | IP Address | Subnet Mask | CIDR | Wildcard Mask | Default Gateway | Usable Host Range | Purpose |
|---|---|---|---|---|---|---|---|---|---|
| **PC1** | Fa0 | `192.168.1.0/24` | `192.168.1.10` | `255.255.255.0` | `/24` | `0.0.0.255` | `192.168.1.1` | `.1` - `.254` | Primary Workstation |
| **PC2** | Fa0 | `192.168.1.0/24` | `192.168.1.11` | `255.255.255.0` | `/24` | `0.0.0.255` | `192.168.1.1` | `.1` - `.254` | Secondary Workstation |
| **Switch-LAN** | VLAN 1 | `192.168.1.0/24` | `192.168.1.2` | `255.255.255.0` | `/24` | `0.0.0.255` | `192.168.1.1` | `.1` - `.254` | L2 LAN Management |
| **R1 (Edge)** | Gig0/0 | `192.168.1.0/24` | `192.168.1.1` | `255.255.255.0` | `/24` | `0.0.0.255` | N/A | `.1` - `.254` | Workstation Default GW |
| **R1 (Edge)** | Gig0/1 | `10.0.1.0/30` | `10.0.1.1` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Primary Core Link (R1 side) |
| **R1 (Edge)** | Gig0/2 | `10.0.2.0/30` | `10.0.2.1` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Backup Core Link (R1 side) |
| **R2 (Core Primary)** | Gig0/1 | `10.0.1.0/30` | `10.0.1.2` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Primary Core Link (R2 side) |
| **R2 (Core Primary)** | Gig0/2 | `10.0.3.0/30` | `10.0.3.1` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Core-to-GW Link (R2 side) |
| **R3 (Core Backup)** | Gig0/1 | `10.0.2.0/30` | `10.0.2.2` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Backup Core Link (R3 side) |
| **R3 (Core Backup)** | Gig0/2 | `10.0.4.0/30` | `10.0.4.1` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Core-to-GW Link (R3 side) |
| **R4 (GW Router)** | Gig0/1 | `10.0.3.0/30` | `10.0.3.2` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Core-to-GW Link (R4 Primary) |
| **R4 (GW Router)** | Gig0/2 | `10.0.4.0/30` | `10.0.4.2` | `255.255.255.252` | `/30` | `0.0.0.3` | N/A | `.1` - `.2` | Core-to-GW Link (R4 Backup) |
| **R4 (GW Router)** | Gig0/0 | `172.16.1.0/24` | `172.16.1.1` | `255.255.255.0` | `/24` | `0.0.0.255` | N/A | `.1` - `.254` | DMZ Server Default GW |
| **Switch-DMZ** | VLAN 1 | `172.16.1.0/24` | `172.16.1.2` | `255.255.255.0` | `/24` | `0.0.0.255` | `172.16.1.1` | `.1` - `.254` | L2 DMZ Management |
| **Server1 (Web)** | Fa0 | `172.16.1.0/24` | `172.16.1.100` | `255.255.255.0` | `/24` | `0.0.0.255` | `172.16.1.1` | `.1` - `.254` | HTTP Web Portal |
| **DNS-Server** | Fa0 | `172.16.1.0/24` | `172.16.1.10` | `255.255.255.0` | `/24` | `0.0.0.255` | `172.16.1.1` | `.1` - `.254` | Domain Name Service |

---

## 3. Subnetting Calculations & Mathematical Proofs

### Subnet A: Workstation LAN (`192.168.1.0/24`)
* **Subnet Mask:** `255.255.255.0` (Binary: `11111111.11111111.11111111.00000000`)
* **Host Bits ($h$):** $32 - 24 = 8$
* **Total Host Addresses:** $2^8 = 256$
* **Usable Host Addresses:** $2^8 - 2 = 254$
* **Network Address:** `192.168.1.0`
* **Broadcast Address:** `192.168.1.255`
* **DHCP Dynamic Pool:** `192.168.1.50` through `192.168.1.150` (101 addresses)

### Subnet B: Server DMZ (`172.16.1.0/24`)
* **Subnet Mask:** `255.255.255.0` (Binary: `11111111.11111111.11111111.00000000`)
* **Host Bits ($h$):** $32 - 24 = 8$
* **Usable Host Addresses:** $254$
* **Network Address:** `172.16.1.0`
* **Broadcast Address:** `172.16.1.255`

### Subnets C, D, E, F: Core Point-to-Point Links (`/30`)
* **Subnet Mask:** `255.255.255.252` (Binary: `11111111.11111111.11111111.11111100`)
* **Host Bits ($h$):** $32 - 30 = 2$
* **Total Host Addresses:** $2^2 = 4$
* **Usable Host Addresses:** $2^2 - 2 = 2$
* **Wildcard Mask:** `0.0.0.3` (used for OSPF network statements)

#### Detailed Breakdowns for `/30` Links:
1. **Subnet C (`10.0.1.0/30`):**
   * Network: `10.0.1.0`, Usable: `10.0.1.1` (R1) and `10.0.1.2` (R2), Broadcast: `10.0.1.3`
2. **Subnet D (`10.0.2.0/30`):**
   * Network: `10.0.2.0`, Usable: `10.0.2.1` (R1) and `10.0.2.2` (R3), Broadcast: `10.0.2.3`
3. **Subnet E (`10.0.3.0/30`):**
   * Network: `10.0.3.0`, Usable: `10.0.3.1` (R2) and `10.0.3.2` (R4), Broadcast: `10.0.3.3`
4. **Subnet F (`10.0.4.0/30`):**
   * Network: `10.0.4.0`, Usable: `10.0.4.1` (R3) and `10.0.4.2` (R4), Broadcast: `10.0.4.3`
