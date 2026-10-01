"""
NetSimX — Device & Node Data Models
Defines classes for Routers, Switches, PCs, and Servers.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List


class NodeType(str, Enum):
    """Categorization of supported network nodes."""
    ROUTER = "ROUTER"
    SWITCH = "SWITCH"
    PC = "PC"
    SERVER = "SERVER"


class DeviceStatus(str, Enum):
    """Operational status of a network device or interface."""
    UP = "UP"
    DOWN = "DOWN"


@dataclass
class Node:
    """Base class for all network devices in NetSimX."""
    node_id: str
    name: str
    node_type: NodeType
    ip_address: str
    subnet_mask: str = "255.255.255.0"
    gateway: Optional[str] = None
    status: DeviceStatus = DeviceStatus.UP
    pos_x: float = 0.0
    pos_y: float = 0.0
    interfaces: List[str] = field(default_factory=list)

    @property
    def is_up(self) -> bool:
        """Returns True if the device is active and operational."""
        return self.status == DeviceStatus.UP


@dataclass
class Router(Node):
    """Layer-3 routing device capable of path forwarding and maintaining a routing table."""
    def __init__(
        self,
        node_id: str,
        name: str,
        ip_address: str,
        subnet_mask: str = "255.255.255.0",
        pos_x: float = 0.0,
        pos_y: float = 0.0
    ):
        super().__init__(
            node_id=node_id,
            name=name,
            node_type=NodeType.ROUTER,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            pos_x=pos_x,
            pos_y=pos_y
        )


@dataclass
class Switch(Node):
    """Layer-2 switching device maintaining MAC-to-port forwarding tables."""
    def __init__(
        self,
        node_id: str,
        name: str,
        ip_address: str = "0.0.0.0",
        pos_x: float = 0.0,
        pos_y: float = 0.0
    ):
        super().__init__(
            node_id=node_id,
            name=name,
            node_type=NodeType.SWITCH,
            ip_address=ip_address,
            pos_x=pos_x,
            pos_y=pos_y
        )


@dataclass
class PC(Node):
    """End-user host workstation acting as traffic source or client."""
    def __init__(
        self,
        node_id: str,
        name: str,
        ip_address: str,
        subnet_mask: str = "255.255.255.0",
        gateway: Optional[str] = None,
        pos_x: float = 0.0,
        pos_y: float = 0.0
    ):
        super().__init__(
            node_id=node_id,
            name=name,
            node_type=NodeType.PC,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            gateway=gateway,
            pos_x=pos_x,
            pos_y=pos_y
        )


@dataclass
class Server(Node):
    """Target destination or enterprise server delivering network services."""
    def __init__(
        self,
        node_id: str,
        name: str,
        ip_address: str,
        subnet_mask: str = "255.255.255.0",
        gateway: Optional[str] = None,
        pos_x: float = 0.0,
        pos_y: float = 0.0
    ):
        super().__init__(
            node_id=node_id,
            name=name,
            node_type=NodeType.SERVER,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            gateway=gateway,
            pos_x=pos_x,
            pos_y=pos_y
        )
