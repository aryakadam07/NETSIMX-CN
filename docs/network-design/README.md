# NETSIMX — Network Design Documentation Suite

**Document ID:** NX-DES-100  
**Author:** Member 1 — Network Architecture, Addressing & Cisco Packet Tracer  
**Git Branch:** `arya`  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  

---

## 👥 Member 1 Ownership & Contribution Overview

As **Member 1**, my assigned technical responsibility encompasses the overall **Network Architecture, IPv4/CIDR Addressing & Cisco Packet Tracer Implementation** for NETSIMX. 

All design decisions, IP plans, router/switch IOS configurations, network services, test matrices, and Packet Tracer lab files are cataloged within this directory (`docs/network-design/`) and `packet-tracer/`.

```
NETSIMX Network Architecture
┌────────────────────────────────────────────────────────────────────────┐
│ WORKSTATION LAN (192.168.1.0/24)  ──► Edge Router R1 (DHCP Server)      │
│                                           │ (Primary: Cost 2.0 / Backup: 4.0)
│                                           ▼                            │
│                                  [ R2 Core ] or [ R3 Backup ]          │
│                                           │                            │
│                                           ▼                            │
│ SERVER DMZ (172.16.1.0/24)        ◄── Gateway Router R4 (DMZ Gateway)  │
│ (Web Portal & DNS Server)                                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Comprehensive Index of Deliverables

| Section | Topic | Documentation Link | Key Contents |
|---|---|---|---|
| **1** | **Executive Analysis** | [`network-design-analysis.md`](network-design-analysis.md) | Requirement analysis, network scope, device inventory, security & design constraints. |
| **2** | **Network Topology** | [`network-topology.md`](network-topology.md) | Hierarchical 3-tier architecture, device roles, link metrics, primary/alternate path models, Mermaid diagram. |
| **3** | **IP Addressing & Subnetting** | [`ip-addressing-plan.md`](ip-addressing-plan.md) | Complete VLSM addressing table (`/24` and `/30` subnets), CIDR math, wildcard masks, host ranges. |
| **4** | **Packet Tracer Project** | [`../../packet-tracer/`](../../packet-tracer/NETSIMX_Network_Design.pkt) | Cisco Packet Tracer topology file (`NETSIMX_Network_Design.pkt`) and IOS configuration files. |
| **5** | **Router Configuration** | [`router-configuration.md`](router-configuration.md) | Cisco IOS CLI scripts for `R1`, `R2`, `R3`, `R4` (Interface IPs, OSPF Area 0, metric tuning, DHCP pools). |
| **6** | **Switch Configuration** | [`switch-configuration.md`](switch-configuration.md) | Layer 2 configuration for `Switch-LAN` and `Switch-DMZ` (VLAN 10/20, portfast, SVIs, default gateways). |
| **7** | **Network Services** | [`network-services.md`](network-services.md) | DHCP leases (`R1`), DNS records (`netsimx.local`), and HTTP Web Portal architecture. |
| **8** | **Connectivity Testing** | [`connectivity-testing.md`](connectivity-testing.md) | 12 systematic test scenarios (ICMP Ping, Traceroute, DNS lookup, HTTP web fetch, failover path check). |
| **9** | **Troubleshooting Guide** | [`troubleshooting.md`](troubleshooting.md) | 5-step OSI diagnostic procedure and solutions for common network/routing/service issues. |

---

## ⚡ Quick Summary of Technical Specifications

1. **Network Topology:** 4 Routers (`R1`, `R2`, `R3`, `R4`), 2 Layer-2 Switches (`Switch-LAN`, `Switch-DMZ`), 2 Workstations (`PC1`, `PC2`), and 2 Servers (`Server1` Web, `DNS-Server`).
2. **Subnetting Scheme:**
   * Workstation LAN: `192.168.1.0/24` (Gateway: `192.168.1.1`)
   * Server DMZ: `172.16.1.0/24` (Gateway: `172.16.1.1`)
   * Core Transit Links: `10.0.1.0/30`, `10.0.2.0/30`, `10.0.3.0/30`, `10.0.4.0/30`
3. **Routing Method:** Dynamic Single-Area OSPF (Area 0) with custom cost metrics (`R1` $\rightarrow$ `R2` $\rightarrow$ `R4` primary cost 6.0; `R1` $\rightarrow$ `R3` $\rightarrow$ `R4` backup cost 10.0).
4. **Network Services Configured:** DHCP Pool on `R1`, DNS Resolution (`netsimx.local` $\rightarrow$ `172.16.1.100`), HTTP Web Portal on `Server1`.
5. **Connectivity Test Result:** **100% PASS** across all 12 test cases.
6. **Cisco Packet Tracer File Location:** [`packet-tracer/NETSIMX_Network_Design.pkt`](../../packet-tracer/NETSIMX_Network_Design.pkt) and [`packet-tracer/configs/`](../../packet-tracer/configs/).
