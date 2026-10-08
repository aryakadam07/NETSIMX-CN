"""
NetSimX — Experiments Panel (Member 4)
Experiment history, results viewing, comparison, and export.
"""

import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QSplitter, QTextEdit, QFileDialog, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from analytics.comparison import ExperimentComparator
from database.models import ExperimentRecord, MetricsRecord


class ExperimentsPanel(QWidget):
    """
    Experiment history panel.
    Shows all saved experiments, allows detailed view, comparison and export.
    """

    def __init__(self, experiment_manager, analytics_panel=None, parent=None):
        super().__init__(parent)
        self._mgr = experiment_manager
        self._analytics = analytics_panel
        self._comparator = ExperimentComparator()
        self._setup_ui()
        self.refresh_table()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: #1A1A2A; color: #CCCCDD;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Experiment History")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf); title.setStyleSheet("color: #EEEEFF;")
        layout.addWidget(title)

        # ── Experiment table ──────────────────────────────────────────
        table_group = QGroupBox("Saved Experiments")
        table_group.setStyleSheet(self._group_style())
        table_layout = QVBoxLayout(table_group)

        # Action buttons
        btn_row = QHBoxLayout()
        self._refresh_btn  = QPushButton("⟳ Refresh")
        self._view_btn     = QPushButton("👁 View")
        self._compare_btn  = QPushButton("⚖ Compare Selected")
        self._export_csv_btn = QPushButton("📄 Export CSV")
        self._export_json_btn = QPushButton("{ } Export JSON")
        self._delete_btn   = QPushButton("🗑 Delete")

        for btn in [self._refresh_btn, self._view_btn, self._compare_btn,
                    self._export_csv_btn, self._export_json_btn, self._delete_btn]:
            btn.setStyleSheet(self._btn_style())
            btn_row.addWidget(btn)
        btn_row.addStretch()
        table_layout.addLayout(btn_row)

        self._exp_table = QTableWidget()
        self._exp_table.setColumnCount(8)
        self._exp_table.setHorizontalHeaderLabels([
            "ID", "Name", "Date", "Algorithm", "Source→Dest",
            "Packets", "Status", "Duration(ms)"
        ])
        self._exp_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._exp_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._exp_table.setStyleSheet(self._table_style())
        self._exp_table.setAlternatingRowColors(True)
        self._exp_table.setMinimumHeight(200)
        table_layout.addWidget(self._exp_table)
        layout.addWidget(table_group)

        # ── Detail view ───────────────────────────────────────────────
        detail_group = QGroupBox("Experiment Details")
        detail_group.setStyleSheet(self._group_style())
        detail_layout = QVBoxLayout(detail_group)
        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setMaximumHeight(150)
        self._detail_text.setStyleSheet(
            "QTextEdit { background: #0A0A1A; color: #AACCAA; "
            "border: 1px solid #333355; font-family: Consolas, monospace; font-size: 9px; }")
        detail_layout.addWidget(self._detail_text)
        layout.addWidget(detail_group)

        # ── Comparison table ──────────────────────────────────────────
        cmp_group = QGroupBox("Side-by-Side Comparison")
        cmp_group.setStyleSheet(self._group_style())
        cmp_layout = QVBoxLayout(cmp_group)
        self._cmp_table = QTableWidget()
        self._cmp_table.setStyleSheet(self._table_style())
        self._cmp_table.setAlternatingRowColors(True)
        self._cmp_table.setMaximumHeight(160)
        cmp_layout.addWidget(self._cmp_table)
        layout.addWidget(cmp_group)

        layout.addStretch()

        # Connect
        self._refresh_btn.clicked.connect(self.refresh_table)
        self._view_btn.clicked.connect(self._view_selected)
        self._compare_btn.clicked.connect(self._compare_selected)
        self._export_csv_btn.clicked.connect(self._export_csv)
        self._export_json_btn.clicked.connect(self._export_json)
        self._delete_btn.clicked.connect(self._delete_selected)

    # ------------------------------------------------------------------
    # Table population
    # ------------------------------------------------------------------

    def refresh_table(self) -> None:
        experiments = self._mgr.list_experiments()
        self._exp_table.setRowCount(len(experiments))
        self._exp_records = experiments

        for row, exp in enumerate(experiments):
            route = f"{exp.source} → {exp.destination}"
            date_short = exp.created_at[:19] if exp.created_at else "—"
            self._exp_table.setItem(row, 0, QTableWidgetItem(exp.id[:8] + "…"))
            self._exp_table.setItem(row, 1, QTableWidgetItem(exp.name))
            self._exp_table.setItem(row, 2, QTableWidgetItem(date_short))
            self._exp_table.setItem(row, 3, QTableWidgetItem(exp.algorithm))
            self._exp_table.setItem(row, 4, QTableWidgetItem(route))
            self._exp_table.setItem(row, 5, QTableWidgetItem(str(exp.packet_count)))
            self._exp_table.setItem(row, 6, QTableWidgetItem(exp.status))
            self._exp_table.setItem(row, 7, QTableWidgetItem(f"{exp.duration_ms:.0f}"))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _get_selected_ids(self) -> List[str]:
        rows = set(i.row() for i in self._exp_table.selectedItems())
        result = []
        for r in sorted(rows):
            if r < len(self._exp_records):
                result.append(self._exp_records[r].id)
        return result

    def _view_selected(self) -> None:
        ids = self._get_selected_ids()
        if not ids:
            self._detail_text.setPlainText("Select an experiment to view.")
            return
        exp_id = ids[0]
        exp = self._mgr.load_experiment(exp_id)
        metrics = self._mgr.get_experiment_metrics(exp_id)
        events = self._mgr.get_experiment_events(exp_id)

        if not exp:
            self._detail_text.setPlainText("Experiment not found.")
            return

        lines = [
            f"ID:           {exp.id}",
            f"Name:         {exp.name}",
            f"Created:      {exp.created_at}",
            f"Algorithm:    {exp.algorithm}",
            f"Route:        {exp.source} → {exp.destination}",
            f"Traffic:      {exp.traffic_level}  ({exp.packet_count} pkts)",
            f"Duration:     {exp.duration_ms:.1f} ms",
            f"Status:       {exp.status}",
            "─" * 50,
        ]

        if metrics:
            lines += [
                f"Packets Sent:      {metrics.packets_sent}",
                f"Delivered:         {metrics.packets_delivered}",
                f"Dropped:           {metrics.packets_dropped}",
                f"PDR:               {metrics.pdr_percent:.2f}%",
                f"Packet Loss:       {metrics.plr_percent:.2f}%",
                f"Throughput:        {metrics.throughput_mbps:.4f} Mbps",
                f"Avg Latency:       {metrics.avg_latency_ms:.3f} ms",
                f"Jitter:            {metrics.jitter_ms:.3f} ms",
            ]
        else:
            lines.append("No metrics recorded.")

        if events:
            lines.append(f"\nEvents ({len(events)}):")
            for ev in events[:10]:
                lines.append(f"  [{ev.timestamp_ms:.0f}ms] {ev.event_type}: {ev.target}")

        self._detail_text.setPlainText("\n".join(lines))

    def _compare_selected(self) -> None:
        ids = self._get_selected_ids()
        if len(ids) < 2:
            QMessageBox.information(self, "Compare", "Select 2 or more experiments to compare.")
            return

        rows_data = []
        for eid in ids:
            exp = self._mgr.load_experiment(eid)
            metrics = self._mgr.get_experiment_metrics(eid)
            if exp:
                row = {
                    "name": exp.name, "algorithm": exp.algorithm,
                    "source": exp.source, "destination": exp.destination,
                    "status": exp.status,
                }
                if metrics:
                    row.update({
                        "packets_sent": metrics.packets_sent,
                        "packets_delivered": metrics.packets_delivered,
                        "packets_dropped": metrics.packets_dropped,
                        "plr_percent": metrics.plr_percent,
                        "pdr_percent": metrics.pdr_percent,
                        "avg_latency_ms": metrics.avg_latency_ms,
                        "jitter_ms": metrics.jitter_ms,
                        "throughput_mbps": metrics.throughput_mbps,
                        "avg_hops": metrics.avg_hops,
                    })
                rows_data.append(row)

        comparison = self._comparator.compare(rows_data)
        headers = self._comparator.get_table_headers()
        table_rows = self._comparator.get_table_rows(comparison)

        self._cmp_table.setColumnCount(len(headers))
        self._cmp_table.setHorizontalHeaderLabels(headers)
        self._cmp_table.setRowCount(len(table_rows))
        self._cmp_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)

        for r, row in enumerate(table_rows):
            for c, val in enumerate(row):
                self._cmp_table.setItem(r, c, QTableWidgetItem(val))

    def _export_csv(self) -> None:
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.information(self, "Export", "Select an experiment first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", f"experiment_{ids[0][:8]}.csv",
            "CSV Files (*.csv)")
        if path:
            self._mgr.export_csv(ids[0], path)
            QMessageBox.information(self, "Export", f"Exported to {path}")

    def _export_json(self) -> None:
        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.information(self, "Export", "Select an experiment first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", f"experiment_{ids[0][:8]}.json",
            "JSON Files (*.json)")
        if path:
            self._mgr.export_json(ids[0], path)
            QMessageBox.information(self, "Export", f"Exported to {path}")

    def _delete_selected(self) -> None:
        ids = self._get_selected_ids()
        if not ids:
            return
        reply = QMessageBox.question(
            self, "Delete",
            f"Delete {len(ids)} experiment(s)? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for eid in ids:
                self._mgr.delete_experiment(eid)
            self.refresh_table()

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    @staticmethod
    def _group_style() -> str:
        return ("QGroupBox { color: #AAAACC; border: 1px solid #444466; "
                "border-radius: 6px; margin-top: 6px; padding-top: 10px; font-size: 10px; }")

    @staticmethod
    def _btn_style() -> str:
        return ("QPushButton { background: #2A2A3E; color: #CCCCDD; border: 1px solid #444466; "
                "border-radius: 4px; padding: 5px 12px; font-size: 9px; }"
                "QPushButton:hover { background: #3A3A5E; }"
                "QPushButton:pressed { background: #4A4A6E; }")

    @staticmethod
    def _table_style() -> str:
        return ("QTableWidget { background: #12121E; color: #CCCCDD; "
                "border: 1px solid #333355; gridline-color: #2A2A3E; font-size: 9px; }"
                "QHeaderView::section { background: #2A2A3E; color: #9999BB; "
                "border: none; padding: 4px; font-size: 9px; }"
                "QTableWidget::item:alternate { background: #1A1A2E; }"
                "QTableWidget::item:selected { background: #3A3A6E; }")
