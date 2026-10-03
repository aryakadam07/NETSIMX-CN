# NETSIMX — Network Design Analysis

**Document ID:** NX-DES-001  
**Author:** Member 1 (Network Architecture, Addressing & Cisco Packet Tracer)  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Branch:** `arya`  
**Status:** Approved  

---

## 1. Executive Overview

NetSimX simulates and manages an enterprise campus computer network with a dual-pillar validation model:
1. **Glass-Box Python Discrete-Event Simulation Engine:** Provides algorithmic transparency, step-by-step priority queue state visualization, drop-tail buffer overflow modeling, traffic burst generation, and failure convergence logging.
2. **Cisco Packet Tracer Physical Baseline Suite:** Validates realistic Cisco IOS protocol behavior (OSPF, RIPv2, 802.1Q VLAN trunking, DHCP, DNS, HTTP, and ICMP CLI operations).

This document summarizes Phase 1 analysis of the existing NETSIMX project architecture, specifications, requirements, constraints, and device allocations based on standard project documentation (`README.md`, `docs/architecture/*`, `core/*`).

---

## 2. Network Type & Objectives

NETSIMX is designed to model an **Enterprise Campus Network & Data Center Gateway** connecting internal user departments to critical network services and external servers through a redundant core routing architecture.

### Primary Objectives:
* **High Availability & Fault Tolerance:** Multi-homed core routers (`R2` and `R3`) provide primary and secondary path forwarding between user LANs and DMZ server networks.
* **Deterministic Subnet Allocation:** Structured IPv4 CIDR addressing scheme supporting VLSM across LAN, DMZ, and point-to-point transit segments.
* **Dynamic Convergence:** Automatic route recalculation via Link-State routing (OSPF Area 0 / Dijkstra algorithm) upon link or router failure.
* **Core Network Services:** Centralized allocation of IP parameters via DHCP, host resolution via DNS, and web portal access via HTTP.

---

## 3. Required Network Devices & Inventory

| Device Category | Quantities | Model / Role in NETSIMX | Key Functions |
|---|---|---|---|
| **Routers** | 4 | Cisco 2911 ISR / Layer 3 Routers (`R1`, `R2`, `R3`, `R4`) | Edge routing, OSPF Area 0, point-to-point transit, DHCP server, ICMP gateway. |
| **Switches** | 2 | Cisco Catalyst 2960 Layer 2 Switches (`Switch-LAN`, `Switch-DMZ`) | Access/Trunk switching, 802.1Q VLAN aggregation, port security. |
| **End-User PCs** | 2+ | Workstations (`PC1`, `PC2`) | Clients in Workstation LAN generating synthetic traffic flows. |
| **Servers** | 2 | Enterprise Servers (`Server1` - Web Portal, `DNS-Server`) | DMZ servers providing HTTP (`172.16.1.100`) and DNS (`172.16.1.10`) services. |

---

## 4. Network Segments & Subnetting Requirements

The campus network is partitioned into six distinct subnets to enforce security boundaries and optimize routing:

1. **Workstation LAN (Subnet A):** `192.168.1.0/24` — Connects `PC1`, `PC2` through `Switch-LAN` to Edge Router `R1` (Gateway `192.168.1.1`).
2. **Server DMZ (Subnet B):** `172.16.1.0/24` — Connects `Server1` (Web) and `DNS-Server` through `Switch-DMZ` to Core Router `R4` (Gateway `172.16.1.1`).
3. **Primary Core Transit Link (Subnet C):** `10.0.1.0/30` — Point-to-point link connecting `R1` (Gig0/1) and `R2` (Gig0/1).
4. **Backup Core Transit Link (Subnet D):** `10.0.2.0/30` — Point-to-point link connecting `R1` (Gig0/2) and `R3` (Gig0/1).
5. **Primary-to-Gateway Core Link (Subnet E):** `10.0.3.0/30` — Point-to-point link connecting `R2` (Gig0/2) and `R4` (Gig0/1).
6. **Backup-to-Gateway Core Link (Subnet F):** `10.0.4.0/30` — Point-to-point link connecting `R3` (Gig0/2) and `R4` (Gig0/2).

---

## 5. Required Routing Architecture

* **Interior Gateway Protocol (IGP):** OSPF Area 0 (Single-Area Backbone OSPF).
* **Metric Tuning:** 
  * `R1-R2` Link Cost = `2.0` (Fast primary path via Core Router R2, total path cost `PC1` $\rightarrow$ `Server1` = 6.0).
  * `R1-R3` Link Cost = `4.0` (Backup alternate path via Core Router R3, total path cost `PC1` $\rightarrow$ `Server1` = 10.0).
* **Dynamic Rerouting Logic:** When link `L_R1_R2` or router `R2` fails, OSPF automatically invalidates the primary path and converges traffic onto the alternate path (`R1` $\rightarrow$ `R3` $\rightarrow$ `R4`).

---

## 6. Required Network Services

1. **DHCP (Dynamic Host Configuration Protocol):**
   * Configured on Edge Router `R1`.
   * Scope: Workstation LAN (`192.168.1.0/24`).
   * Pool Range: `192.168.1.50` to `192.168.1.150`.
   * Default Gateway: `192.168.1.1`, DNS Server: `172.16.1.10`.
2. **DNS (Domain Name System):**
   * Provided by `DNS-Server` at `172.16.1.10`.
   * Domain Record: `netsimx.local` $\rightarrow$ `172.16.1.100`.
3. **HTTP (Web Service):**
   * Provided by `Server1` at `172.16.1.100`.
   * Hosts the NetSimX System Status & Telemetry Dashboard web page.

---

## 7. Security & Constraint Specifications

* **Isolated Git Workspace:** Member 1 work strictly maintained on branch `arya`.
* **Standard CIDR Subnetting:** Full compliance with standard IPv4 masks (`/24` for LANs, `/30` for inter-router point-to-point links).
* **Zero Duplication / Collision:** Guaranteed unique host IP allocation across all interfaces.
* **Cisco IOS Syntax Compliance:** All configuration runbooks utilize production-grade Cisco IOS command syntax compatible with Packet Tracer 8.2+.
