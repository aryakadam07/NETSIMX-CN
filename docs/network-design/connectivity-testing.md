# NETSIMX — Connectivity & Protocol Verification Plan

**Document ID:** NX-DES-008  
**Author:** Member 1 (Network Architecture, Addressing & Cisco Packet Tracer)  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Branch:** `arya`  
**Status:** Verified & Passed  

---

## 1. Test Methodology & Scope

Systematic connectivity testing was conducted across all network segments in both Cisco Packet Tracer (Simulation & Real-Time Modes) and automated Python validation scripts (`pytest`).

### Testing Categories:
1. **Intra-Subnet Connectivity:** Verification within local broadcast domains.
2. **Gateway Reachability:** Host-to-Router default gateway ICMP echo checks.
3. **Inter-Subnet Core Routing:** End-to-end multi-hop ICMP ping and traceroute path tracking.
4. **Fault Recovery & Dynamic Failover:** Path verification during link shutdown (`L_R1_R2` DOWN).
5. **Application Services:** DHCP address acquisition, DNS A-record resolution, and HTTP web page fetching.

---

## 2. Comprehensive Test Results Table

| Test ID | Source Device | Destination Device | Test Type / Command | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| **TST-01** | PC1 (`192.168.1.10`) | Edge Router R1 (`192.168.1.1`) | `ping 192.168.1.1` | 4/4 ICMP Replies, RTT < 2ms | 4/4 ICMP Replies, RTT = 1ms | **PASS** |
| **TST-02** | PC1 (`192.168.1.10`) | PC2 (`192.168.1.11`) | `ping 192.168.1.11` | 4/4 ICMP Replies (Same LAN) | 4/4 ICMP Replies, RTT = 1ms | **PASS** |
| **TST-03** | PC1 (`192.168.1.10`) | Core Router R2 (`10.0.1.2`) | `ping 10.0.1.2` | 4/4 ICMP Replies via R1 | 4/4 ICMP Replies, RTT = 5ms | **PASS** |
| **TST-04** | PC1 (`192.168.1.10`) | Core Router R3 (`10.0.2.2`) | `ping 10.0.2.2` | 4/4 ICMP Replies via R1 | 4/4 ICMP Replies, RTT = 6ms | **PASS** |
| **TST-05** | PC1 (`192.168.1.10`) | Gateway Router R4 (`172.16.1.1`) | `ping 172.16.1.1` | 4/4 ICMP Replies via Primary Path | 4/4 ICMP Replies, RTT = 12ms | **PASS** |
| **TST-06** | PC1 (`192.168.1.10`) | Server1 (`172.16.1.100`) | `ping 172.16.1.100` | 4/4 ICMP Replies (End-to-End) | 4/4 ICMP Replies, RTT = 15ms | **PASS** |
| **TST-07** | Server1 (`172.16.1.100`) | PC1 (`192.168.1.10`) | `ping 192.168.1.10` | 4/4 Reverse ICMP Replies | 4/4 ICMP Replies, RTT = 15ms | **PASS** |
| **TST-08** | PC1 (`192.168.1.10`) | Server1 (`172.16.1.100`) | `tracert 172.16.1.100` | Path: `192.168.1.1` $\rightarrow$ `10.0.1.2` $\rightarrow$ `10.0.3.2` $\rightarrow$ `172.16.1.100` | Primary Path Hops Verified | **PASS** |
| **TST-09** | PC1 (Dynamic IP) | Router R1 | DHCP Discover/Request | Receives IP `192.168.1.50`, GW `192.168.1.1`, DNS `172.16.1.10` | IP parameters leased cleanly | **PASS** |
| **TST-10** | PC1 (`192.168.1.10`) | DNS-Server (`172.16.1.10`) | `nslookup netsimx.local` | Resolves to `172.16.1.100` | `172.16.1.100` returned | **PASS** |
| **TST-11** | PC1 (`192.168.1.10`) | Server1 (`172.16.1.100`) | HTTP Browser Request | HTTP 200 OK — Renders NetSimX Portal | Web page loaded successfully | **PASS** |
| **TST-12** | PC1 (During R1-R2 Cut) | Server1 (`172.16.1.100`) | `tracert 172.16.1.100` | Reroutes: `192.168.1.1` $\rightarrow$ `10.0.2.2` $\rightarrow$ `10.0.4.2` $\rightarrow$ `172.16.1.100` | Backup Path via R3 Verified | **PASS** |

---

## 3. Detailed Traceroute Output Analysis

### Primary Path Execution (Normal Operation)
```text
C:\> tracert 172.16.1.100

Tracing route to 172.16.1.100 over a maximum of 30 hops:

  1     1 ms     1 ms     1 ms  192.168.1.1 (Edge Router R1)
  2     5 ms     4 ms     5 ms  10.0.1.2    (Primary Core Router R2)
  3    10 ms    11 ms    10 ms  10.0.3.2    (Gateway Router R4)
  4    14 ms    15 ms    14 ms  172.16.1.100 (Server1 Web Portal)

Trace complete.
```

### Alternate Path Execution (After Injecting `L_R1_R2` Shutdown)
```text
C:\> tracert 172.16.1.100

Tracing route to 172.16.1.100 over a maximum of 30 hops:

  1     1 ms     1 ms     1 ms  192.168.1.1 (Edge Router R1)
  2     7 ms     6 ms     7 ms  10.0.2.2    (Backup Core Router R3)
  3    14 ms    13 ms    14 ms  10.0.4.2    (Gateway Router R4)
  4    18 ms    19 ms    18 ms  172.16.1.100 (Server1 Web Portal)

Trace complete.
```

---

## 4. Verification Summary

All 12 test cases achieved a 100% **PASS** rate. OSPF Area 0 metric tuning correctly prioritizes the primary low-cost path (R2) during normal operations and seamlessly failovers to the backup path (R3) upon interface shutdown.
