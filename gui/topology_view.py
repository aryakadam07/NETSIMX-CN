"""
NetSimX — Topology View (Member 4)
Interactive QGraphicsScene displaying nodes, links, status and route highlighting.
"""

from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsRectItem, QGraphicsItem,
    QLabel, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QPen, QBrush, QColor, QFont, QWheelEvent, QPainter
)

from visualization.topology_visualizer import TopologyVisualizer


class ZoomableGraphicsView(QGraphicsView):
    """QGraphicsView with mouse-wheel zoom and middle-button pan."""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet("background: #12121E; border: none;")
        self._zoom = 1.0

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._zoom *= factor
        self._zoom = max(0.2, min(self._zoom, 5.0))
        self.scale(factor, factor)


class TopologyView(QWidget):
    """
    Interactive network topology canvas.
    Draws nodes as coloured shapes, links as lines.
    Supports path highlighting, status updates, zoom and pan.
    """

    node_selected = pyqtSignal(str)  # emits node_id
    link_selected = pyqtSignal(str)  # emits link_id

    def __init__(self, topology_adapter, parent=None):
        super().__init__(parent)
        self._topo = topology_adapter
        self._positions: Dict[str, tuple] = {}
        self._node_items: Dict[str, QGraphicsEllipseItem] = {}
        self._link_items: Dict[str, QGraphicsLineItem] = {}
        self._label_items: Dict[str, QGraphicsTextItem] = {}
        self._highlighted_path: List[str] = []
        self._setup_ui()
        self.refresh_topology()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: #12121E;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background: #1E1E2E; border-bottom: 1px solid #333355;")
        toolbar.setMaximumHeight(36)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)

        lbl = QLabel("Network Topology")
        lbl.setStyleSheet("color: #AAAACC; font-size: 11px; font-weight: bold;")
        tb_layout.addWidget(lbl)
        tb_layout.addStretch()

        refresh_btn = QPushButton("⟳ Refresh")
        refresh_btn.setStyleSheet(
            "QPushButton { background: #2A2A3E; color: #9999CC; border: 1px solid #444466; "
            "border-radius: 4px; padding: 2px 10px; font-size: 10px; }"
            "QPushButton:hover { background: #3A3A5E; }"
        )
        refresh_btn.clicked.connect(self.refresh_topology)
        tb_layout.addWidget(refresh_btn)

        reset_btn = QPushButton("Reset Zoom")
        reset_btn.setStyleSheet(refresh_btn.styleSheet())
        reset_btn.clicked.connect(self._reset_zoom)
        tb_layout.addWidget(reset_btn)

        layout.addWidget(toolbar)

        # Scene and view
        self._scene = QGraphicsScene()
        self._scene.setBackgroundBrush(QBrush(QColor("#12121E")))
        self._view = ZoomableGraphicsView(self._scene)
        layout.addWidget(self._view)

    # ------------------------------------------------------------------
    # Topology rendering
    # ------------------------------------------------------------------

    def refresh_topology(self) -> None:
        """Re-reads topology from adapter and redraws everything."""
        self._scene.clear()
        self._node_items.clear()
        self._link_items.clear()
        self._label_items.clear()

        nodes = self._topo.get_nodes()
        links = self._topo.get_links()

        if not nodes:
            self._scene.addText("No topology loaded", QFont()).setDefaultTextColor(
                QColor("#555577"))
            return

        # Compute positions
        self._positions = TopologyVisualizer.compute_positions(nodes, links)

        # Draw links first (behind nodes)
        for link in links:
            self._draw_link(link)

        # Draw nodes on top
        for node in nodes:
            self._draw_node(node)

        self._view.fitInView(self._scene.itemsBoundingRect(),
                             Qt.AspectRatioMode.KeepAspectRatio)

    def _draw_node(self, node: dict) -> None:
        nid = node["id"]
        x, y = self._positions.get(nid, (100, 100))
        r = TopologyVisualizer.NODE_RADIUS
        color = TopologyVisualizer.node_color(node["type"], node["is_up"])

        ellipse = QGraphicsEllipseItem(x - r, y - r, 2 * r, 2 * r)
        ellipse.setBrush(QBrush(QColor(color)))
        border_color = "#FFFFFF" if node["is_up"] else "#FF4444"
        ellipse.setPen(QPen(QColor(border_color), 1.5))
        ellipse.setZValue(2)
        ellipse.setData(0, nid)  # store node_id
        ellipse.setToolTip(
            f"{node['name']} ({node['type']})\nIP: {node['ip']}\nStatus: {node['status']}")

        self._scene.addItem(ellipse)
        self._node_items[nid] = ellipse

        # Type icon label inside node
        icon_map = {"ROUTER": "R", "SWITCH": "S", "PC": "P", "SERVER": "Sv"}
        icon = icon_map.get(node["type"], "?")
        icon_text = self._scene.addText(icon)
        icon_font = QFont()
        icon_font.setPointSize(8)
        icon_font.setBold(True)
        icon_text.setFont(icon_font)
        icon_text.setDefaultTextColor(QColor("#FFFFFF"))
        icon_text.setPos(x - icon_text.boundingRect().width() / 2,
                         y - icon_text.boundingRect().height() / 2)
        icon_text.setZValue(3)

        # Name label below node
        name_text = self._scene.addText(node["name"])
        name_font = QFont()
        name_font.setPointSize(7)
        name_text.setFont(name_font)
        name_text.setDefaultTextColor(QColor("#CCCCDD"))
        name_text.setPos(x - name_text.boundingRect().width() / 2, y + r + 2)
        name_text.setZValue(3)
        self._label_items[nid] = name_text

    def _draw_link(self, link: dict) -> None:
        lid = link["id"]
        src = link["source"]
        dst = link["destination"]
        x1, y1 = self._positions.get(src, (0, 0))
        x2, y2 = self._positions.get(dst, (0, 0))

        in_path = self._is_in_path(src, dst)
        color = TopologyVisualizer.link_color(link["is_up"], in_path)
        width = 3.0 if in_path else (1.0 if link["is_up"] else 1.5)
        style = Qt.PenStyle.SolidLine if link["is_up"] else Qt.PenStyle.DashLine

        pen = QPen(QColor(color), width, style)
        line = self._scene.addLine(x1, y1, x2, y2, pen)
        line.setZValue(1)
        line.setData(0, lid)
        line.setToolTip(
            f"Link: {src} ↔ {dst}\nCost: {link['cost']} | "
            f"BW: {link['bandwidth_mbps']} Mbps | Delay: {link['delay_ms']} ms")
        self._link_items[lid] = line

        # Cost label at midpoint
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        cost_text = self._scene.addText(f"{link['cost']:.0f}")
        cost_font = QFont()
        cost_font.setPointSize(6)
        cost_text.setFont(cost_font)
        cost_text.setDefaultTextColor(QColor("#666688"))
        cost_text.setPos(mx, my)
        cost_text.setZValue(1)

    # ------------------------------------------------------------------
    # Path highlighting
    # ------------------------------------------------------------------

    def highlight_path(self, path: List[str]) -> None:
        """Highlights nodes and links along a route."""
        self._highlighted_path = path
        self.refresh_topology()

    def clear_highlights(self) -> None:
        self._highlighted_path = []
        self.refresh_topology()

    def _is_in_path(self, src: str, dst: str) -> bool:
        if len(self._highlighted_path) < 2:
            return False
        for i in range(len(self._highlighted_path) - 1):
            a, b = self._highlighted_path[i], self._highlighted_path[i + 1]
            if (a == src and b == dst) or (a == dst and b == src):
                return True
        return False

    # ------------------------------------------------------------------
    # Status updates
    # ------------------------------------------------------------------

    def update_node_status(self, node_id: str, is_up: bool) -> None:
        """Updates a node's visual colour without full redraw."""
        node_item = self._node_items.get(node_id)
        if node_item:
            node = next((n for n in self._topo.get_nodes() if n["id"] == node_id), None)
            if node:
                color = TopologyVisualizer.node_color(node["type"], is_up)
                node_item.setBrush(QBrush(QColor(color)))
                node_item.setPen(QPen(QColor("#FF4444" if not is_up else "#FFFFFF"), 1.5))

    def update_link_status(self, link_id: str, is_up: bool) -> None:
        """Updates a link's visual style without full redraw."""
        link_item = self._link_items.get(link_id)
        if link_item:
            color = TopologyVisualizer.LINK_DOWN_COLOR if not is_up else TopologyVisualizer.LINK_COLOR
            style = Qt.PenStyle.DashLine if not is_up else Qt.PenStyle.SolidLine
            link_item.setPen(QPen(QColor(color), 1.5, style))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset_zoom(self) -> None:
        self._view.resetTransform()
        self._view.fitInView(self._scene.itemsBoundingRect(),
                             Qt.AspectRatioMode.KeepAspectRatio)
