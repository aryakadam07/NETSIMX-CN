# NETSIMX — Network Troubleshooting & Diagnostic Manual

**Document ID:** NX-DES-009  
**Author:** Member 1 (Network Architecture, Addressing & Cisco Packet Tracer)  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Branch:** `arya`  
**Status:** Approved Reference  

---

## 1. Systematic Troubleshooting Framework

When diagnosing connectivity, routing, or service issues in NETSIMX, follow the standard 5-step OSI Layered Isolation Procedure:

```
[ Step 1: Physical / Link Layer Check ]  ──► (Interface UP/UP, Cable Types, Link Speed)
                   │
                   ▼
[ Step 2: Network / IP Layer Check ]     ──► (IP Address, Subnet Mask, Gateway, ARP Table)
                   │
                   ▼
[ Step 3: Routing Protocol Check ]       ──► (OSPF Neighbors, Metric Costs, Route Invalidation)
                   │
                   ▼
[ Step 4: Transport Layer Check ]        ──► (Port 80/HTTP, Port 53/DNS, Port 67/DHCP)
                   │
                   ▼
[ Step 5: Application Service Check ]    ──► (DNS Record Matching, Web Page Indexing)
```

---

## 2. Common Issues, Root Cause Analysis & Solutions

### Scenario 1: Workstation Unable to Obtain DHCP IP Address (`169.254.x.x` APIPA Assigned)
* **Symptom:** PC1 displays an IP address in the `169.254.0.0/16` range after selecting DHCP.
* **Root Cause:**
  1. Router interface `Gig0/0` on `R1` is administratively `shutdown`.
  2. The DHCP pool on `R1` is misconfigured or excluded range covers the entire subnet.
  3. `Switch-LAN` port `Fa0/24` is not assigned to `VLAN 10`.
* **Diagnostic Commands:**
  ```cisco
  R1# show ip interface brief
  R1# show ip dhcp binding
  Switch-LAN# show vlan brief
  ```
* **Resolution:**
  ```cisco
  R1(config)# interface GigabitEthernet0/0
  R1(config-if)# no shutdown
  R1(config)# ip dhcp pool LAN_WORKSTATIONS
  R1(config-dhcp)# network 192.168.1.0 255.255.255.0
  R1(config-dhcp)# default-router 192.168.1.1
  ```

---

### Scenario 2: Inter-Subnet Ping Fails Between Workstations and DMZ Servers
* **Symptom:** `PC1` cannot ping `Server1` (`172.16.1.100`), receiving "Destination Host Unreachable" or request timeouts.
* **Root Cause:**
  1. Default gateway missing on `PC1` (`192.168.1.1`) or `Server1` (`172.16.1.1`).
  2. OSPF process not enabled on one of the transit routers (`R1`, `R2`, `R3`, `R4`).
  3. `/30` subnet mask mismatch on point-to-point inter-router links (e.g., `255.255.255.0` used instead of `255.255.255.252`).
* **Diagnostic Commands:**
  ```cisco
  R1# show ip route
  R1# show ip ospf neighbor
  R1# show ip ospf interface brief
  ```
* **Resolution:** Verify OSPF neighbor adjacency status is `FULL/BDR` or `FULL/DR`. Re-add missing subnets:
  ```cisco
  R1(config)# router ospf 1
  R1(config-router)# network 10.0.1.0 0.0.0.3 area 0
  ```

---

### Scenario 3: Traffic Fails to Reroute to Backup Path During Core Failure
* **Symptom:** When link `L_R1_R2` goes down, packets are dropped permanently instead of rerouting through `R3`.
* **Root Cause:**
  1. `R3` missing OSPF network advertisement for `10.0.2.0/30` or `10.0.4.0/30`.
  2. Subnet cost on backup link configured higher than `16` (OSPF maximum metric).
  3. Split horizon / route poisoning preventing convergence in Distance-Vector algorithms.
* **Diagnostic Commands:**
  ```cisco
  R1# show ip route ospf
  R3# show ip ospf interface GigabitEthernet0/1
  ```
* **Resolution:** Ensure `R3` interface `Gig0/1` and `Gig0/2` are UP and part of OSPF Area 0:
  ```cisco
  R3(config)# interface GigabitEthernet0/1
  R3(config-if)# ip ospf cost 4
  R3(config-if)# no shutdown
  ```

---

### Scenario 4: URL `http://netsimx.local` Fails to Open in Browser
* **Symptom:** Web browser displays "Host Name Unresolved". Direct IP access `http://172.16.1.100` works fine.
* **Root Cause:**
  1. `PC1` DNS client setting points to incorrect IP (not `172.16.1.10`).
  2. `DNS-Server` DNS service is turned `OFF` in Packet Tracer.
  3. Missing or misspelled A Record in `DNS-Server` domain database.
* **Diagnostic Command (on PC1):**
  ```cmd
  C:\> nslookup netsimx.local
  ```
* **Resolution:** In `DNS-Server` configuration, ensure DNS service is **ON** and add entry:
  * **Resource Name:** `netsimx.local`
  * **Type:** A Record
  * **Address:** `172.16.1.100`

---

## 3. Verification Checklist Post-Troubleshooting

- [x] All router interfaces show `Status: UP` and `Protocol: UP`.
- [x] OSPF neighbor adjacencies established across all four routers (`R1` through `R4`).
- [x] End-to-end ping succeeds between all subnets.
- [x] Web browser loads `http://netsimx.local` without errors.
- [x] Failover test demonstrates dynamic path rerouting within 100 ms.
