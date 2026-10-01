"""
NetSimX — Network Topology Manager
Encapsulates network nodes, links, and graph theory representations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from core.node import Node, DeviceStatus
from core.link import Link


@dataclass
class NetworkTopology:
    """In-memory container and graph manager for network devices and links."""
    network_id: str
    name: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    links: Dict[str, Link] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        """Adds a device to the topology."""
        self.nodes[node.node_id] = node

    def remove_node(self, node_id: str) -> None:
        """Removes a device and all incident links."""
        if node_id in self.nodes:
            del self.nodes[node_id]
        # Remove incident links
        links_to_remove = [
            link_id for link_id, link in self.links.items()
            if link.source == node_id or link.destination == node_id
        ]
        for link_id in links_to_remove:
            del self.links[link_id]

    def add_link(self, link: Link) -> None:
        """Adds a communication channel."""
        self.links[link.link_id] = link

    def remove_link(self, link_id: str) -> None:
        """Removes a link by ID."""
        if link_id in self.links:
            del self.links[link_id]

    def set_node_status(self, node_id: str, status: DeviceStatus) -> None:
        """Sets node status to UP or DOWN."""
        if node_id in self.nodes:
            self.nodes[node_id].status = status

    def set_link_status(self, link_id: str, status: DeviceStatus) -> None:
        """Sets link status to UP or DOWN."""
        if link_id in self.links:
            self.links[link_id].status = status

    def get_active_adjacency_dict(self) -> Dict[str, Dict[str, float]]:
        """
        Returns an adjacency list for routing algorithms:
        {src_id: {dst_id: cost}}
        Filters out any nodes or links currently DOWN.
        Treats links as bidirectional communication channels.
        """
        active_nodes = {nid for nid, n in self.nodes.items() if n.is_up}
        graph: Dict[str, Dict[str, float]] = {nid: {} for nid in active_nodes}

        for link in self.links.values():
            if not link.is_up:
                continue
            u, v = link.source, link.destination
            if u in active_nodes and v in active_nodes:
                # Add forward edge
                graph[u][v] = link.cost
                # Add reverse edge for full-duplex communication
                graph[v][u] = link.cost

        return graph

    def get_link_between(self, u: str, v: str) -> Optional[Link]:
        """Finds the active link connecting nodes u and v."""
        for link in self.links.values():
            if (link.source == u and link.destination == v) or (link.source == v and link.destination == u):
                return link
        return None
