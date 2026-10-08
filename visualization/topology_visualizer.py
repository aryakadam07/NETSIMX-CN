"""
NetSimX — Topology Layout Helper (Member 4)
Uses NetworkX to compute node positions for rendering in QGraphicsScene.
"""

from typing import Dict, Tuple, List, Optional, Any
import logging

logger = logging.getLogger("TopologyVisualizer")


class TopologyVisualizer:
    """
    Computes layout positions for network topology nodes.
    Uses NetworkX spring_layout when available, falls back to grid.
    """

    # Visual constants
    CANVAS_W = 900
    CANVAS_H = 550
    NODE_RADIUS = 24
    MARGIN = 60

    # Node type colours (hex strings)
    NODE_COLORS = {
        "ROUTER": "#4A90D9",
        "SWITCH": "#7B68EE",
        "PC":     "#5CB85C",
        "SERVER": "#E8A838",
    }
    NODE_DOWN_COLOR = "#CC3333"
    LINK_COLOR = "#888888"
    LINK_DOWN_COLOR = "#CC3333"
    PATH_COLOR = "#00CC66"

    @staticmethod
    def compute_positions(nodes: List[Dict[str, Any]],
                          links: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
        """
        Returns {node_id: (x, y)} scaled to canvas dimensions.
        Uses NetworkX spring_layout if available, else pre-assigned pos_x/pos_y,
        else falls back to a circle layout.
        """
        # Prefer pre-assigned positions from topology if set
        positions: Dict[str, Tuple[float, float]] = {}
        has_positions = all(n.get("pos_x", 0) != 0 or n.get("pos_y", 0) != 0 for n in nodes)

        if has_positions:
            for n in nodes:
                positions[n["id"]] = (float(n["pos_x"]), float(n["pos_y"]))
            return positions

        # Try NetworkX spring layout
        try:
            import networkx as nx  # type: ignore
            G = nx.Graph()
            for n in nodes:
                G.add_node(n["id"])
            for l in links:
                G.add_edge(l["source"], l["destination"], weight=l.get("cost", 1.0))

            W = TopologyVisualizer.CANVAS_W - 2 * TopologyVisualizer.MARGIN
            H = TopologyVisualizer.CANVAS_H - 2 * TopologyVisualizer.MARGIN
            raw = nx.spring_layout(G, seed=42, k=1.5)
            for nid, (rx, ry) in raw.items():
                x = TopologyVisualizer.MARGIN + (rx + 1) / 2 * W
                y = TopologyVisualizer.MARGIN + (ry + 1) / 2 * H
                positions[nid] = (x, y)
            return positions
        except ImportError:
            pass

        # Fallback: evenly spaced circle
        import math
        n_count = len(nodes)
        cx = TopologyVisualizer.CANVAS_W / 2
        cy = TopologyVisualizer.CANVAS_H / 2
        r = min(cx, cy) - TopologyVisualizer.MARGIN
        for i, n in enumerate(nodes):
            angle = (2 * math.pi * i) / max(n_count, 1)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            positions[n["id"]] = (x, y)

        return positions

    @staticmethod
    def node_color(node_type: str, is_up: bool) -> str:
        if not is_up:
            return TopologyVisualizer.NODE_DOWN_COLOR
        return TopologyVisualizer.NODE_COLORS.get(node_type.upper(), "#888888")

    @staticmethod
    def link_color(is_up: bool, in_path: bool) -> str:
        if in_path:
            return TopologyVisualizer.PATH_COLOR
        if not is_up:
            return TopologyVisualizer.LINK_DOWN_COLOR
        return TopologyVisualizer.LINK_COLOR
