"""
NetSimX — Routing Panel (Member 4 / Redesign)
Calls Member 2's routing engine and displays the calculated path in charcoal & emerald aesthetic.
"""

from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from gui.styles import (
    MAIN_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR, TEXT_PRIMARY,
    TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL,
    get_groupbox_stylesheet, get_input_stylesheet, get_button_stylesheet,
    get_secondary_button_stylesheet, get_table_stylesheet, get_text_edit_stylesheet
)


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
        self.setStyleSheet(f"background-color: {MAIN_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Routing Algorithms & Path Calculation")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        # ── Controls ──────────────────────────────────────────────────
        ctrl_group = QGroupBox("Route Configuration")
        ctrl_group.setStyleSheet(get_groupbox_stylesheet())
        ctrl_layout = QVBoxLayout(ctrl_group)
        ctrl_layout.setSpacing(10)

        def _row(label_text, widget):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setMinimumWidth(110)
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
            row.addWidget(lbl)
            row.addWidget(widget)
            row.addStretch()
            return row

        self._src_combo = QComboBox()
        self._dst_combo = QComboBox()
        self._algo_combo = QComboBox()

        for w in [self._src_combo, self._dst_combo, self._algo_combo]:
            w.setStyleSheet(get_input_stylesheet())
            w.setMinimumWidth(200)

        self._algo_combo.addItems(self._routing.get_available_algorithms())

        ctrl_layout.addLayout(_row("Source Node:", self._src_combo))
        ctrl_layout.addLayout(_row("Destination Node:", self._dst_combo))
        ctrl_layout.addLayout(_row("Routing Algorithm:", self._algo_combo))

        calc_btn = QPushButton("Calculate Route")
        calc_btn.setStyleSheet(get_button_stylesheet(ACCENT_EMERALD, "#101010"))
        calc_btn.clicked.connect(self._calculate)
        ctrl_layout.addWidget(calc_btn)

        layout.addWidget(ctrl_group)

        # ── Result ────────────────────────────────────────────────────
        res_group = QGroupBox("Route Calculation Result")
        res_group.setStyleSheet(get_groupbox_stylesheet())
        res_layout = QVBoxLayout(res_group)

        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMinimumHeight(110)
        self._result_text.setMaximumHeight(150)
        self._result_text.setStyleSheet(get_text_edit_stylesheet(ACCENT_EMERALD))
        res_layout.addWidget(self._result_text)
        layout.addWidget(res_group)

        # ── Routing table ─────────────────────────────────────────────
        rt_group = QGroupBox("Router Routing Table Inspector")
        rt_group.setStyleSheet(get_groupbox_stylesheet())
        rt_layout = QVBoxLayout(rt_group)

        rt_header_row = QHBoxLayout()
        rt_lbl = QLabel("Target Router:")
        rt_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self._router_combo = QComboBox()
        self._router_combo.setStyleSheet(get_input_stylesheet())
        self._router_combo.setMinimumWidth(160)

        show_rt_btn = QPushButton("Show Table")
        show_rt_btn.setStyleSheet(get_secondary_button_stylesheet())
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
        self._rt_table.setStyleSheet(get_table_stylesheet())
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
            self._result_text.setStyleSheet(get_text_edit_stylesheet(ACCENT_EMERALD))
        else:
            text = (
                f"SOURCE:       {src}\n"
                f"DESTINATION:  {dst}\n"
                f"ALGORITHM:    {algo}\n"
                f"─────────────────────────\n"
                f"STATUS:       UNREACHABLE\n"
                f"REASON:       {result.get('error', 'No route available')}\n"
            )
            self._result_text.setStyleSheet(get_text_edit_stylesheet(ACCENT_CORAL))

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
