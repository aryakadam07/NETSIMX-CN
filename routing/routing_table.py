"""
NetSimX — Router Routing Table & Longest-Prefix Matching Subsystem (Member 2)
Provides data structures and lookup logic for IP prefixes, default routes,
metric comparison, and deterministic route selection.
"""

from dataclasses import dataclass
import ipaddress
from typing import List, Optional, Dict, Any


@dataclass
class RoutingEntry:
    """
    Represents a single entry (route) in a router's routing table.
    
    Attributes:
        destination (str): Network CIDR (e.g. '192.168.1.0/24'), Host IP/CIDR (e.g. '10.0.0.1/32'),
                           or symbolic Node ID (e.g. 'Server1').
        next_hop (str): Next-hop router ID or IP address (e.g. 'R2' or '10.0.1.1').
        metric (float): Path metric/cost to destination.
        interface (Optional[str]): Outgoing interface name or Link ID (e.g. 'L_R1_R2' or 'eth0').
        prefix_length (int): Prefix mask length (e.g. 24 for /24). Auto-derived if CIDR provided.
        protocol (str): Route source protocol ('CONNECTED', 'STATIC', 'DIJKSTRA', 'BELLMAN_FORD', 'DV').
        is_active (bool): Operational status of this route.
    """
    destination: str
    next_hop: str
    metric: float = 0.0
    interface: Optional[str] = None
    prefix_length: int = 0
    protocol: str = "STATIC"
    is_active: bool = True

    def __post_init__(self):
        # Auto-calculate prefix_length if destination is a valid IPv4 CIDR string
        if self.prefix_length == 0 and "/" in self.destination:
            try:
                net = ipaddress.ip_network(self.destination, strict=False)
                self.prefix_length = net.prefixlen
            except ValueError:
                pass


class RoutingTable:
    """
    Implements a Layer-3 router routing table supporting:
    - Add, update, delete routes
    - Longest-prefix matching (LPM) via Python ipaddress standard library
    - Metric-based route selection & deterministic tie-breaking
    - Default route matching (0.0.0.0/0)
    - ASCII table formatting for display and debugging
    """

    def __init__(self, router_id: str = "Router"):
        self.router_id = router_id
        # Internal storage: map destination string to RoutingEntry
        self._entries: Dict[str, RoutingEntry] = {}

    def add_route(self, entry: RoutingEntry) -> bool:
        """
        Adds a new route entry or updates an existing route if the new route offers
        a better metric for the exact same destination prefix.
        
        Returns:
            bool: True if route was added/updated, False if rejected (e.g. higher cost existing route).
        """
        dest = entry.destination
        if dest in self._entries:
            existing = self._entries[dest]
            # Replace if new route has lower metric or higher prefix specificity
            if entry.metric < existing.metric or entry.prefix_length > existing.prefix_length:
                self._entries[dest] = entry
                return True
            return False
        
        self._entries[dest] = entry
        return True

    def remove_route(self, destination: str) -> bool:
        """
        Deletes a route entry by exact destination string match.
        
        Returns:
            bool: True if deleted, False if destination not found.
        """
        if destination in self._entries:
            del self._entries[destination]
            return True
        return False

    def update_route(self, entry: RoutingEntry) -> bool:
        """
        Unconditionally replaces/updates the route entry for the target destination.
        """
        self._entries[entry.destination] = entry
        return True

    def get_route(self, destination: str) -> Optional[RoutingEntry]:
        """Returns exact route entry by destination key, if present."""
        return self._entries.get(destination)

    def get_all_routes(self) -> List[RoutingEntry]:
        """Returns a list of all active routing entries."""
        return [entry for entry in self._entries.values() if entry.is_active]

    def clear(self) -> None:
        """Clears all entries from the routing table."""
        self._entries.clear()

    def lookup(self, destination_address: str) -> Optional[RoutingEntry]:
        """
        Performs Longest-Prefix Matching (LPM) for a target destination.
        
        Route Selection Order:
        1. Longest Prefix Length (highest prefix_length)
        2. Lowest Metric (lowest total path cost)
        3. Deterministic Tie-Breaker (lexicographical order of next_hop)
        
        Supports:
        - Exact string matching for symbolic Node IDs (e.g., 'Server1', 'R4')
        - Standard IPv4 IP address matching against CIDR subnets (e.g., '10.10.10.25' vs '10.10.10.0/24')
        - Default route ('0.0.0.0/0') fallback
        
        Args:
            destination_address (str): Target IP address or node ID.
            
        Returns:
            Optional[RoutingEntry]: Winning routing table entry, or None if unreachable.
        """
        active_entries = self.get_all_routes()
        if not active_entries:
            return None

        # 1. First check: Direct symbolic node ID match (e.g., 'Server1' or 'R3')
        symbolic_matches = [e for e in active_entries if e.destination == destination_address]
        if symbolic_matches:
            # Tie-break by lowest metric
            symbolic_matches.sort(key=lambda e: (e.metric, e.next_hop))
            return symbolic_matches[0]

        # 2. Try parsing destination_address as an IPv4 Address
        try:
            target_ip = ipaddress.ip_address(destination_address)
        except ValueError:
            # Not a valid IP address string, return None as unreachable
            return None

        matching_candidates: List[RoutingEntry] = []

        for entry in active_entries:
            try:
                network = ipaddress.ip_network(entry.destination, strict=False)
                if target_ip in network:
                    matching_candidates.append(entry)
            except ValueError:
                # Destination string in entry is not a valid IP network format
                continue

        if not matching_candidates:
            return None

        # Sort candidates according to strict decision tree:
        # Priority 1: Prefix length descending (-prefix_length)
        # Priority 2: Metric ascending (metric)
        # Priority 3: Deterministic tie-breaker (next_hop lexicographical)
        matching_candidates.sort(
            key=lambda e: (-e.prefix_length, e.metric, e.next_hop)
        )

        return matching_candidates[0]

    def display_table(self) -> str:
        """Generates a formatted ASCII table representation of the routing table."""
        header = f"=== Routing Table for Router [{self.router_id}] ==="
        cols = f"{'Destination':<18} | {'Prefix':<6} | {'Next Hop':<10} | {'Metric':<8} | {'Interface':<10} | {'Protocol':<10}"
        sep = "-" * len(cols)

        lines = [header, sep, cols, sep]
        for entry in sorted(self._entries.values(), key=lambda e: (e.destination, e.metric)):
            if entry.is_active:
                iface = entry.interface if entry.interface else "N/A"
                lines.append(
                    f"{entry.destination:<18} | /{entry.prefix_length:<5} | {entry.next_hop:<10} | "
                    f"{entry.metric:<8.1f} | {iface:<10} | {entry.protocol:<10}"
                )
        if len(lines) <= 4:
            lines.append("  [Table is empty]")
        lines.append(sep)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.display_table()
