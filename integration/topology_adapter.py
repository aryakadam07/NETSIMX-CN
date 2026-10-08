"""
NetSimX — Topology Adapter (Member 4)
Wraps core/network.py NetworkTopology for use by GUI and adapters.
Provides dict-based node/link summaries safe to use in UI widgets.
"""

from typing import List, Dict, Optional, Any
import logging

from core.network import NetworkTopology
from core.node import Node, NodeType, DeviceStatus, Router, Switch, PC, Server
from core.link import Link

logger = logging.getLogger("TopologyAdapter")


class TopologyAdapter:
    """
    Thin wrapper around NetworkTopology.
    Provides UI-friendly dict representations and a demo topology factory.
    """

    def __init__(self, topology: Optional[NetworkTopology] = None):
        self._topology: NetworkTopology = topology or self.create_demo_topology()

    # ------------------------------------------------------------------
    # Topology accessor
    # ------------------------------------------------------------------

    def set_topology(self, topology: NetworkTopology) -> None:
        self._topology = topology

    def get_topology(self) -> NetworkTopology:
        return self._topology

    # ------------------------------------------------------------------
    # Node API
    # ------------------------------------------------------------------

    def get_nodes(self) -> List[Dict[str, Any]]:
        """Returns list of node info dicts suitable for UI widgets."""
        result = []
        for nid, node in self._topology.nodes.items():
            result.append({
                "id": nid,
                "name": node.name,
                "type": node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type),
                "ip": node.ip_address,
                "status": node.status.value if hasattr(node.status, "value") else str(node.status),
                "is_up": node.is_up,
                "pos_x": node.pos_x,
                "pos_y": node.pos_y,
            })
        return result

    def get_node_ids(self) -> List[str]:
        return list(self._topology.nodes.keys())

    def get_node_status(self, node_id: str) -> str:
        node = self._topology.nodes.get(node_id)
        if node is None:
            return "UNKNOWN"
        return node.status.value if hasattr(node.status, "value") else str(node.status)

    def set_node_status(self, node_id: str, is_up: bool) -> bool:
        if node_id not in self._topology.nodes:
            return False
        status = DeviceStatus.UP if is_up else DeviceStatus.DOWN
        self._topology.set_node_status(node_id, status)
        return True

    # ------------------------------------------------------------------
    # Link API
    # ------------------------------------------------------------------

    def get_links(self) -> List[Dict[str, Any]]:
        """Returns list of link info dicts suitable for UI widgets."""
        result = []
        for lid, link in self._topology.links.items():
            result.append({
                "id": lid,
                "source": link.source,
                "destination": link.destination,
                "cost": link.cost,
                "bandwidth_mbps": link.bandwidth_mbps,
                "delay_ms": link.delay_ms,
                "loss_probability": link.loss_probability,
                "status": link.status.value if hasattr(link.status, "value") else str(link.status),
                "is_up": link.is_up,
                "queue_capacity": link.queue_capacity,
            })
        return result

    def get_link_ids(self) -> List[str]:
        return list(self._topology.links.keys())

    def get_link_status(self, link_id: str) -> str:
        link = self._topology.links.get(link_id)
        if link is None:
            return "UNKNOWN"
        return link.status.value if hasattr(link.status, "value") else str(link.status)

    def set_link_status(self, link_id: str, is_up: bool) -> bool:
        if link_id not in self._topology.links:
            return False
        status = DeviceStatus.UP if is_up else DeviceStatus.DOWN
        self._topology.set_link_status(link_id, status)
        return True

    # ------------------------------------------------------------------
    # Graph API
    # ------------------------------------------------------------------

    def get_adjacency_graph(self) -> Dict[str, Dict[str, float]]:
        """Returns active adjacency dict for routing algorithms."""
        return self._topology.get_active_adjacency_dict()

    def get_topology_stats(self) -> Dict[str, int]:
        """Returns node/link counts by type for the dashboard."""
        nodes = list(self._topology.nodes.values())
        links = list(self._topology.links.values())
        return {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "routers": sum(1 for n in nodes if n.node_type == NodeType.ROUTER),
            "switches": sum(1 for n in nodes if n.node_type == NodeType.SWITCH),
            "pcs": sum(1 for n in nodes if n.node_type == NodeType.PC),
            "servers": sum(1 for n in nodes if n.node_type == NodeType.SERVER),
            "active_nodes": sum(1 for n in nodes if n.is_up),
            "active_links": sum(1 for l in links if l.is_up),
            "failed_nodes": sum(1 for n in nodes if not n.is_up),
            "failed_links": sum(1 for l in links if not l.is_up),
        }

    # ------------------------------------------------------------------
    # Demo topology factory
    # ------------------------------------------------------------------

    @staticmethod
    def create_demo_topology() -> NetworkTopology:
        """
        Creates the reference NETSIMX topology:
        PC1 -- SW1 -- R1 -- R2 -- Server1
                       |         |
                      R3 ------- R4
        Based on the network-design docs (192.168.x.x addressing).
        """
        topo = NetworkTopology(network_id="demo", name="NETSIMX Demo Network")

        # Nodes
        nodes = [
            PC("PC1",      "PC1",      "192.168.1.10",  gateway="192.168.1.1",  pos_x=50,  pos_y=300),
            Switch("SW1",  "SW1",                                                pos_x=200, pos_y=300),
            Router("R1",   "R1",       "192.168.1.1",                           pos_x=350, pos_y=300),
            Router("R2",   "R2",       "10.0.12.2",                             pos_x=550, pos_y=200),
            Router("R3",   "R3",       "10.0.13.3",                             pos_x=550, pos_y=400),
            Router("R4",   "R4",       "10.0.24.4",                             pos_x=700, pos_y=300),
            Server("Server1","Server1","172.16.1.100", gateway="172.16.1.1",    pos_x=850, pos_y=300),
        ]
        for node in nodes:
            topo.add_node(node)

        # Links
        links = [
            Link("L_PC1_SW1",    "PC1",     "SW1",     cost=1.0,  bandwidth_mbps=100, delay_ms=2),
            Link("L_SW1_R1",     "SW1",     "R1",      cost=1.0,  bandwidth_mbps=100, delay_ms=2),
            Link("L_R1_R2",      "R1",      "R2",      cost=2.0,  bandwidth_mbps=100, delay_ms=10),
            Link("L_R1_R3",      "R1",      "R3",      cost=4.0,  bandwidth_mbps=100, delay_ms=20),
            Link("L_R2_R4",      "R2",      "R4",      cost=1.0,  bandwidth_mbps=100, delay_ms=5),
            Link("L_R3_R4",      "R3",      "R4",      cost=1.0,  bandwidth_mbps=100, delay_ms=5),
            Link("L_R4_Server1", "R4",      "Server1", cost=1.0,  bandwidth_mbps=100, delay_ms=5),
        ]
        for link in links:
            topo.add_link(link)

        logger.info("Demo topology created: 7 nodes, 7 links")
        return topo
