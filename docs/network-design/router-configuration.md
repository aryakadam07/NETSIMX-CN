# NETSIMX — Router Configuration Documentation

**Document ID:** NX-DES-005  
**Author:** Member 1 (Network Architecture, Addressing & Cisco Packet Tracer)  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Branch:** `arya`  
**Status:** Approved Baseline  

---

## 1. Overview & Cisco IOS Configuration Architecture

This document presents the complete router configurations for all four routers (`R1`, `R2`, `R3`, `R4`) in the NETSIMX campus topology.

### Router Responsibilities:
* **R1 (Edge Router):** Manages the `192.168.1.0/24` Workstation LAN, provides DHCP address pool leases, and runs single-area OSPF (Area 0) with custom cost metrics (`Cost 2` to R2, `Cost 4` to R3).
* **R2 (Primary Core Router):** Primary forwarding path connecting `R1` and `R4` (`Cost 2` per link, total path cost = 6.0).
* **R3 (Backup Core Router):** Secondary failover path connecting `R1` and `R4` (`Cost 4` per link, total path cost = 10.0).
* **R4 (DMZ Gateway Router):** Connects core transit links to the `172.16.1.0/24` Server DMZ.

---

## 2. Router R1 — Edge Router & DHCP Server

### Device Properties
* **Hostname:** `R1`
* **Model:** Cisco 2911 ISR
* **Purpose:** Edge ingress for Workstation LAN, DHCP pool server, OSPF Area 0 participant.

### Interface & IP Allocation
* **GigabitEthernet0/0:** `192.168.1.1/24` (Gateway for Workstation LAN)
* **GigabitEthernet0/1:** `10.0.1.1/30` (Primary link to R2, OSPF Cost = 2)
* **GigabitEthernet0/2:** `10.0.2.1/30` (Backup link to R3, OSPF Cost = 4)

### Cisco IOS Configuration Commands
```cisco
enable
configure terminal
hostname R1

! Configure DHCP Pool for Workstations
ip dhcp excluded-address 192.168.1.1 192.168.1.49
ip dhcp pool LAN_WORKSTATIONS
 network 192.168.1.0 255.255.255.0
 default-router 192.168.1.1
 dns-server 172.16.1.10
 domain-name netsimx.local
 exit

! Interface Gig0/0 Configuration
interface GigabitEthernet0/0
 description Connected to Switch-LAN (Workstation Subnet)
 ip address 192.168.1.1 255.255.255.0
 no shutdown
 exit

! Interface Gig0/1 Configuration (Primary Core)
interface GigabitEthernet0/1
 description Primary Core Transit Link to R2
 ip address 10.0.1.1 255.255.255.252
 ip ospf cost 2
 no shutdown
 exit

! Interface Gig0/2 Configuration (Backup Core)
interface GigabitEthernet0/2
 description Backup Core Transit Link to R3
 ip address 10.0.2.1 255.255.255.252
 ip ospf cost 4
 no shutdown
 exit

! OSPF Area 0 Configuration
router ospf 1
 router-id 1.1.1.1
 network 192.168.1.0 0.0.0.255 area 0
 network 10.0.1.0 0.0.0.3 area 0
 network 10.0.2.0 0.0.0.3 area 0
 passive-interface GigabitEthernet0/0
 exit

do write memory
```

---

## 3. Router R2 — Primary Core Router

### Device Properties
* **Hostname:** `R2`
* **Model:** Cisco 2911 ISR
* **Purpose:** High-capacity primary transit router.

### Interface & IP Allocation
* **GigabitEthernet0/1:** `10.0.1.2/30` (Link from R1, OSPF Cost = 2)
* **GigabitEthernet0/2:** `10.0.3.1/30` (Link to R4, OSPF Cost = 2)

### Cisco IOS Configuration Commands
```cisco
enable
configure terminal
hostname R2

! Interface Gig0/1 Configuration
interface GigabitEthernet0/1
 description Primary Core Transit Link from R1
 ip address 10.0.1.2 255.255.255.252
 ip ospf cost 2
 no shutdown
 exit

! Interface Gig0/2 Configuration
interface GigabitEthernet0/2
 description Primary Core Transit Link to R4
 ip address 10.0.3.1 255.255.255.252
 ip ospf cost 2
 no shutdown
 exit

! OSPF Area 0 Configuration
router ospf 1
 router-id 2.2.2.2
 network 10.0.1.0 0.0.0.3 area 0
 network 10.0.3.0 0.0.0.3 area 0
 exit

do write memory
```

---

## 4. Router R3 — Backup Core Router

### Device Properties
* **Hostname:** `R3`
* **Model:** Cisco 2911 ISR
* **Purpose:** Secondary failover core router.

### Interface & IP Allocation
* **GigabitEthernet0/1:** `10.0.2.2/30` (Link from R1, OSPF Cost = 4)
* **GigabitEthernet0/2:** `10.0.4.1/30` (Link to R4, OSPF Cost = 4)

### Cisco IOS Configuration Commands
```cisco
enable
configure terminal
hostname R3

! Interface Gig0/1 Configuration
interface GigabitEthernet0/1
 description Backup Core Transit Link from R1
 ip address 10.0.2.2 255.255.255.252
 ip ospf cost 4
 no shutdown
 exit

! Interface Gig0/2 Configuration
interface GigabitEthernet0/2
 description Backup Core Transit Link to R4
 ip address 10.0.4.1 255.255.255.252
 ip ospf cost 4
 no shutdown
 exit

! OSPF Area 0 Configuration
router ospf 1
 router-id 3.3.3.3
 network 10.0.2.0 0.0.0.3 area 0
 network 10.0.4.0 0.0.0.3 area 0
 exit

do write memory
```

---

## 5. Router R4 — Gateway Router (DMZ)

### Device Properties
* **Hostname:** `R4`
* **Model:** Cisco 2911 ISR
* **Purpose:** Gateway for DMZ Server Farm (`172.16.1.0/24`).

### Interface & IP Allocation
* **GigabitEthernet0/0:** `172.16.1.1/24` (Gateway for DMZ Server Farm)
* **GigabitEthernet0/1:** `10.0.3.2/30` (Primary link from R2, OSPF Cost = 2)
* **GigabitEthernet0/2:** `10.0.4.2/30` (Backup link from R3, OSPF Cost = 4)

### Cisco IOS Configuration Commands
```cisco
enable
configure terminal
hostname R4

! Interface Gig0/0 Configuration (DMZ Gateway)
interface GigabitEthernet0/0
 description Connected to Switch-DMZ (Server Subnet)
 ip address 172.16.1.1 255.255.255.0
 no shutdown
 exit

! Interface Gig0/1 Configuration (Primary Core)
interface GigabitEthernet0/1
 description Primary Core Transit Link from R2
 ip address 10.0.3.2 255.255.255.252
 ip ospf cost 2
 no shutdown
 exit

! Interface Gig0/2 Configuration (Backup Core)
interface GigabitEthernet0/2
 description Backup Core Transit Link from R3
 ip address 10.0.4.2 255.255.255.252
 ip ospf cost 4
 no shutdown
 exit

! OSPF Area 0 Configuration
router ospf 1
 router-id 4.4.4.4
 network 172.16.1.0 0.0.0.255 area 0
 network 10.0.3.0 0.0.0.3 area 0
 network 10.0.4.0 0.0.0.3 area 0
 passive-interface GigabitEthernet0/0
 exit

do write memory
```
