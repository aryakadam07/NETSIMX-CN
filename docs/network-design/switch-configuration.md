# NETSIMX — Switch Configuration Documentation

**Document ID:** NX-DES-006  
**Author:** Member 1 (Network Architecture, Addressing & Cisco Packet Tracer)  
**Project:** NetSimX — Intelligent Network Design, Simulation & Performance Analysis System  
**Branch:** `arya`  
**Status:** Approved Baseline  

---

## 1. Executive Summary & Switching Design

The NETSIMX campus switching infrastructure utilizes Layer 2 Cisco Catalyst 2960 switches to aggregate end-user workstations and DMZ enterprise servers.

### Key Switching Principles:
* **VLAN Segmentation:** Workstation traffic is assigned to `VLAN 10 WORKSTATIONS`, while server traffic resides on `VLAN 20 SERVERS`.
* **PortFast Enforcement:** Access ports connecting workstations and servers have Spanning Tree `portfast` enabled to bypass listening/learning states and immediately transition to forwarding.
* **In-Band Management:** Switches maintain management IP interfaces on `VLAN 1` with configured default gateways for administrative accessibility.

---

## 2. Switch-LAN — Workstation Access Switch

### Device Properties
* **Hostname:** `Switch-LAN`
* **Model:** Cisco Catalyst 2960
* **Management IP:** `192.168.1.2/24`
* **Default Gateway:** `192.168.1.1`

### Port Allocation Table
| Interface | Connected Device | Mode | VLAN Assignment | Features |
|---|---|---|---|---|
| `FastEthernet0/1` | PC1 | Access | VLAN 10 WORKSTATIONS | Spanning-Tree PortFast |
| `FastEthernet0/2` | PC2 | Access | VLAN 10 WORKSTATIONS | Spanning-Tree PortFast |
| `FastEthernet0/24` | Router R1 (Gig0/0) | Access / Uplink | VLAN 10 WORKSTATIONS | Uplink to Edge Router |
| `Vlan1` | Management | SVI | VLAN 1 | Management IP: `192.168.1.2` |

### Cisco IOS Configuration Commands
```cisco
enable
configure terminal
hostname Switch-LAN

! Create Workstation VLAN
vlan 10
 name WORKSTATIONS
 exit

! Configure Access Ports
interface FastEthernet0/1
 description Access Port - Workstation PC1
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 exit

interface FastEthernet0/2
 description Access Port - Workstation PC2
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 exit

! Configure Uplink Port to Edge Router R1
interface FastEthernet0/24
 description Uplink Port to Edge Router R1 (Gig0/0)
 switchport mode access
 switchport access vlan 10
 exit

! Management SVI & Default Gateway
interface Vlan1
 description Switch Management Interface
 ip address 192.168.1.2 255.255.255.0
 no shutdown
 exit

ip default-gateway 192.168.1.1

do write memory
```

---

## 3. Switch-DMZ — Server DMZ Access Switch

### Device Properties
* **Hostname:** `Switch-DMZ`
* **Model:** Cisco Catalyst 2960
* **Management IP:** `172.16.1.2/24`
* **Default Gateway:** `172.16.1.1`

### Port Allocation Table
| Interface | Connected Device | Mode | VLAN Assignment | Features |
|---|---|---|---|---|
| `FastEthernet0/1` | Server1 (Web) | Access | VLAN 20 SERVERS | Spanning-Tree PortFast |
| `FastEthernet0/2` | DNS-Server | Access | VLAN 20 SERVERS | Spanning-Tree PortFast |
| `FastEthernet0/24` | Router R4 (Gig0/0) | Access / Uplink | VLAN 20 SERVERS | Uplink to Gateway Router |
| `Vlan1` | Management | SVI | VLAN 1 | Management IP: `172.16.1.2` |

### Cisco IOS Configuration Commands
```cisco
enable
configure terminal
hostname Switch-DMZ

! Create Server DMZ VLAN
vlan 20
 name SERVERS
 exit

! Configure Access Ports
interface FastEthernet0/1
 description Access Port - Web Server Server1
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast
 exit

interface FastEthernet0/2
 description Access Port - DNS Server
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast
 exit

! Configure Uplink Port to Gateway Router R4
interface FastEthernet0/24
 description Uplink Port to Gateway Router R4 (Gig0/0)
 switchport mode access
 switchport access vlan 20
 exit

! Management SVI & Default Gateway
interface Vlan1
 description Switch Management Interface
 ip address 172.16.1.2 255.255.255.0
 no shutdown
 exit

ip default-gateway 172.16.1.1

do write memory
```
