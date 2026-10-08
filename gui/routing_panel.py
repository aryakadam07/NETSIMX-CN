"""
NetSimX — Routing Panel (Member 4)
Calls Member 2's routing engine and displays the calculated path.
"""

from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class RoutingPanel(QWidget):
    """Routing control: select source/dest/algorithm, calculate, display result."""

    route_calculated = pyqtSignal(dict)  # emits route result dict

    def __init__(self, topology_adapter, routing_adapter,
                 topology_view=None, parent=None):
        super().__init__(parent)
        self._topo = topology_adapter
        self._routing = routing_adapter
        self._topology_view = topology_view
        self._setup_ui()
        self._populate_nodes()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: #1A1A2A; color: #CCCCDD;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Route Calculator")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet("color: #EEEEFF;")
        layout.addWidget(title)

        # ── Controls ──────────────────────────────────────────────────
        ctrl_group = QGroupBox("Route Configuration")
        ctrl_group.setStyleSheet(self._group_style())
        ctrl_layout = QVBoxLayout(ctrl_group)
        ctrl_layout.setSpacing(8)

        def _row(label_text, widget):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setMinimumWidth(100)
            lbl.setStyleSheet("color: #9999BB; font-size: 10px;")
            row.addWidget(lbl)
            row.addWidget(widget)
            row.addStretch()
            return row

        self._src_combo = QComboBox()
        self._dst_combo = QComboBox()
        self._algo_combo = QComboBox()

        for w in [self._src_combo, self._dst_combo, self._algo_combo]:
            w.setStyleSheet(self._combo_style())
            w.setMinimumWidth(180)

        self._algo_combo.addItems(self._routing.get_available_algorithms())

        ctrl_layout.addLayout(_row("Source:", self._src_combo))
        ctrl_layout.addLayout(_row("Destination:", self._dst_combo))
        ctrl_layout.addLayout(_row("Algorithm:", self._algo_combo))

        calc_btn = QPushButton("▶  Calculate Route")
        calc_btn.setStyleSheet(self._btn_style("#4A90D9"))
        calc_btn.clicked.connect(self._calculate)
        ctrl_layout.addWidget(calc_btn)

        layout.addWidget(ctrl_group)

        # ── Result ────────────────────────────────────────────────────
        res_group = QGroupBox("Route Result")
        res_group.setStyleSheet(self._group_style())
        res_layout = QVBoxLayout(res_group)

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMinimumHeight(100)
        self._result_text.setMaximumHeight(140)
        self._result_text.setStyleSheet(
            "QTextEdit { background: #12121E; color: #AAFFAA; "
            "border: 1px solid #333355; border-radius: 4px; font-family: Consolas, monospace; font-size: 10px; }"
        )
        res_layout.addWidget(self._result_text)
        layout.addWidget(res_group)

        # ── Routing table ─────────────────────────────────────────────
        rt_group = QGroupBox("Routing Table (selected router)")
        rt_group.setStyleSheet(self._group_style())
        rt_layout = QVBoxLayout(rt_group)

        rt_header_row = QHBoxLayout()
        rt_lbl = QLabel("Router:")
        rt_lbl.setStyleSheet("color: #9999BB; font-size: 10px;")
        self._router_combo = QComboBox()
        self._router_combo.setStyleSheet(self._combo_style())
        self._router_combo.setMinimumWidth(140)
        show_rt_btn = QPushButton("Show Table")
        show_rt_btn.setStyleSheet(self._btn_style("#555577"))
        show_rt_btn.clicked.connect(self._show_routing_table)
        rt_header_row.addWidget(rt_lbl)
        rt_header_row.addWidget(self._router_combo)
        rt_header_row.addWidget(show_rt_btn)
        rt_header_row.addStretch()
        rt_layout.addLayout(rt_header_row)

        self._rt_table = QTableWidget()
        self._rt_table.setColumnCount(5)
        self._rt_table.setHorizontalHeaderLabels(
            ["Destination", "Next Hop", "Metric", "Interface", "Protocol"])
        self._rt_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._rt_table.setStyleSheet(self._table_style())
        self._rt_table.setAlternatingRowColors(True)
        self._rt_table.setMaximumHeight(200)
        rt_layout.addWidget(self._rt_table)
        layout.addWidget(rt_group)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def _populate_nodes(self) -> None:
        node_ids = self._topo.get_node_ids()
        self._src_combo.clear()
        self._dst_combo.clear()
        self._router_combo.clear()
        self._src_combo.addItems(node_ids)
        self._dst_combo.addItems(node_ids)
        if len(node_ids) > 1:
            self._dst_combo.setCurrentIndex(len(node_ids) - 1)

        # Populate router combo with only routers
        routers = [n["id"] for n in self._topo.get_nodes()
                   if n["type"] == "ROUTER"]
        self._router_combo.addItems(routers if routers else node_ids)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _calculate(self) -> None:
        src = self._src_combo.currentText()
        dst = self._dst_combo.currentText()
        algo = self._algo_combo.currentText()

        if not src or not dst:
            self._result_text.setPlainText("Error: Select source and destination.")
            return
        if src == dst:
            self._result_text.setPlainText("Error: Source and destination must differ.")
            return

        result = self._routing.find_route(src, dst, algo)

        if result["reachable"]:
            path_str = " → ".join(result["path"])
            text = (
                f"SOURCE:       {src}\n"
                f"DESTINATION:  {dst}\n"
                f"ALGORITHM:    {result['algorithm']}\n"
                f"─────────────────────────\n"
                f"PATH:         {path_str}\n"
                f"COST:         {result['cost']:.2f}\n"
                f"HOPS:         {result['hops']}\n"
                f"NEXT HOP:     {result['next_hop']}\n"
            )
            self._result_text.setStyleSheet(
                "QTextEdit { background: #0A1A0A; color: #55FF77; "
                "border: 1px solid #226622; border-radius: 4px; "
                "font-family: Consolas, monospace; font-size: 10px; }"
            )
        else:
            text = (
                f"SOURCE:       {src}\n"
                f"DESTINATION:  {dst}\n"
                f"ALGORITHM:    {algo}\n"
                f"─────────────────────────\n"
                f"STATUS:       UNREACHABLE\n"
                f"REASON:       {result.get('error', 'No route available')}\n"
            )
            self._result_text.setStyleSheet(
                "QTextEdit { background: #1A0A0A; color: #FF7755; "
                "border: 1px solid #662222; border-radius: 4px; "
                "font-family: Consolas, monospace; font-size: 10px; }"
            )

        self._result_text.setPlainText(text)

        # Highlight path on topology view
        if self._topology_view and result["reachable"]:
            self._topology_view.highlight_path(result["path"])
        elif self._topology_view:
            self._topology_view.clear_highlights()

        self.route_calculated.emit(result)

    def _show_routing_table(self) -> None:
        router_id = self._router_combo.currentText()
        algo = self._algo_combo.currentText()
        if not router_id:
            return
        rows = self._routing.build_routing_table(router_id, algo)
        self._rt_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self._rt_table.setItem(i, 0, QTableWidgetItem(row["destination"]))
            self._rt_table.setItem(i, 1, QTableWidgetItem(row["next_hop"]))
            self._rt_table.setItem(i, 2, QTableWidgetItem(f"{row['metric']:.1f}"))
            self._rt_table.setItem(i, 3, QTableWidgetItem(row["interface"]))
            self._rt_table.setItem(i, 4, QTableWidgetItem(row["protocol"]))

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    @staticmethod
    def _group_style() -> str:
        return ("QGroupBox { color: #AAAACC; border: 1px solid #444466; "
                "border-radius: 6px; margin-top: 6px; padding-top: 10px; font-size: 10px; }")

    @staticmethod
    def _combo_style() -> str:
        return ("QComboBox { background: #2A2A3E; color: #CCCCDD; "
                "border: 1px solid #444466; border-radius: 4px; padding: 3px 8px; font-size: 10px; }"
                "QComboBox::drop-down { border: none; }"
                "QComboBox QAbstractItemView { background: #2A2A3E; color: #CCCCDD; }")

    @staticmethod
    def _btn_style(bg: str) -> str:
        return (f"QPushButton {{ background: {bg}; color: #FFFFFF; "
                "border: none; border-radius: 4px; padding: 6px 16px; font-size: 10px; font-weight: bold; }"
                "QPushButton:hover { opacity: 0.85; }"
                "QPushButton:pressed { opacity: 0.7; }")

    @staticmethod
    def _table_style() -> str:
        return ("QTableWidget { background: #12121E; color: #CCCCDD; "
                "border: 1px solid #333355; gridline-color: #2A2A3E; font-size: 9px; }"
                "QHeaderView::section { background: #2A2A3E; color: #9999BB; "
                "border: none; padding: 4px; font-size: 9px; }"
                "QTableWidget::item:alternate { background: #1A1A2E; }")
