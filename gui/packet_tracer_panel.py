"""
NetSimX — Cisco Packet Tracer Labs Panel (Member 1 & 4 Redesign)
Interactive lab browser displaying Packet Tracer labs, manuals, and IOS configurations.
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QTextEdit, QPushButton, QSplitter, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.styles import (
    MAIN_BG, CARD_BG, CONTAINER_BG, BORDER_COLOR, TEXT_PRIMARY,
    TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, get_button_stylesheet,
    get_secondary_button_stylesheet, get_groupbox_stylesheet, get_text_edit_stylesheet
)
from config.settings import PATHS


class PacketTracerPanel(QWidget):
    """
    Cisco Packet Tracer Lab Suite Browser.
    Exposes all 9 Packet Tracer labs and configuration scripts.
    """

    LABS = [
        {"id": "Lab 01", "name": "Basic IP Connectivity", "desc": "Peer-to-peer and switch-based LAN verification (ARP, ICMP ping)."},
        {"id": "Lab 02", "name": "IPv4 Subnetting & VLSM", "desc": "VLSM subnet planning across workstation LAN and DMZ server networks."},
        {"id": "Lab 03", "name": "VLANs & Inter-VLAN Routing", "desc": "Router-on-a-Stick (802.1Q encapsulation) and Access/Trunk ports."},
        {"id": "Lab 04", "name": "Static Routing & Default Routes", "desc": "Manual route entry with default gateways and floating static routes."},
        {"id": "Lab 05", "name": "RIPv2 Dynamic Routing", "desc": "Distance-vector dynamic routing configuration and convergence."},
        {"id": "Lab 06", "name": "OSPF Single-Area Area 0", "desc": "Single-area Link-State routing with wildcard masks and cost tuning."},
        {"id": "Lab 07", "name": "Simulation Mode PDU Inspection", "desc": "Hop-by-hop PDU inspection through OSI layers in Packet Tracer."},
        {"id": "Lab 08", "name": "Link & Router Failure Failover", "desc": "Administrative shutdown of interfaces to observe failover rerouting."},
        {"id": "Lab 09", "name": "Dynamic Convergence Comparison", "desc": "Comparing RIP vs OSPF convergence times under dynamic fault injection."},
    ]

    CONFIG_FILES = {
        "Edge Router R1": "packet-tracer/configs/R1.cfg",
        "Primary Core R2": "packet-tracer/configs/R2.cfg",
        "Backup Core R3": "packet-tracer/configs/R3.cfg",
        "Gateway Router R4": "packet-tracer/configs/R4.cfg",
        "Switch-LAN": "packet-tracer/configs/Switch1.cfg",
        "Switch-DMZ": "packet-tracer/configs/Switch2.cfg",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"background-color: {MAIN_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        title = QLabel("Cisco Packet Tracer Lab Suite")
        tf = QFont(); tf.setPointSize(14); tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        sub = QLabel("Explore physical lab runbooks, IOS configuration scripts, and baseline .pkt topologies.")
        sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(sub)

        # Splitter for Lab Selector & Config Viewer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {BORDER_COLOR}; }}")

        # ── Left Pane: Labs List ─────────────────────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)

        labs_group = QGroupBox("Available Experiments (Lab 01 – Lab 09)")
        labs_group.setStyleSheet(get_groupbox_stylesheet())
        lg_layout = QVBoxLayout(labs_group)

        self._lab_list = QListWidget()
        self._lab_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {CONTAINER_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {BORDER_COLOR};
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {CARD_BG};
                color: {ACCENT_EMERALD};
                font-weight: bold;
                border-left: 3px solid {ACCENT_EMERALD};
            }}
            QListWidget::item:hover {{
                background-color: #2A2A2A;
            }}
        """)

        for lab in self.LABS:
            item = QListWidgetItem(f"{lab['id']} — {lab['name']}")
            item.setData(Qt.ItemDataRole.UserRole, lab)
            self._lab_list.addItem(item)

        self._lab_list.currentItemChanged.connect(self._on_lab_selected)
        lg_layout.addWidget(self._lab_list)
        left_layout.addWidget(labs_group)
        splitter.addWidget(left_widget)

        # ── Right Pane: Details & Configuration Viewer ───────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)

        # Lab Detail Card
        detail_group = QGroupBox("Lab Overview & Objectives")
        detail_group.setStyleSheet(get_groupbox_stylesheet())
        dg_layout = QVBoxLayout(detail_group)

        self._detail_title = QLabel("Select a lab on the left")
        self._detail_title.setStyleSheet(f"color: {ACCENT_EMERALD}; font-size: 13px; font-weight: bold;")
        dg_layout.addWidget(self._detail_title)

        self._detail_desc = QLabel("")
        self._detail_desc.setWordWrap(True)
        self._detail_desc.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px;")
        dg_layout.addWidget(self._detail_desc)
        right_layout.addWidget(detail_group)

        # Config Script Selector
        cfg_group = QGroupBox("Cisco IOS Startup Configurations")
        cfg_group.setStyleSheet(get_groupbox_stylesheet())
        cfg_layout = QVBoxLayout(cfg_group)

        cfg_btn_row = QHBoxLayout()
        for device_name, rel_path in self.CONFIG_FILES.items():
            btn = QPushButton(device_name)
            btn.setStyleSheet(get_secondary_button_stylesheet())
            btn.clicked.connect(lambda checked, p=rel_path, d=device_name: self._load_config_file(p, d))
            cfg_btn_row.addWidget(btn)
        cfg_layout.addLayout(cfg_btn_row)

        self._cfg_viewer = QTextEdit()
        self._cfg_viewer.setReadOnly(True)
        self._cfg_viewer.setStyleSheet(get_text_edit_stylesheet(ACCENT_EMERALD))
        cfg_layout.addWidget(self._cfg_viewer)

        right_layout.addWidget(cfg_group)
        splitter.addWidget(right_widget)

        splitter.setSizes([320, 680])
        layout.addWidget(splitter)

        # Select first lab by default
        if self._lab_list.count() > 0:
            self._lab_list.setCurrentRow(0)

    def _on_lab_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if not current:
            return
        lab = current.data(Qt.ItemDataRole.UserRole)
        if lab:
            self._detail_title.setText(f"{lab['id']} — {lab['name']}")
            self._detail_desc.setText(
                f"Description:\n{lab['desc']}\n\n"
                f"Packet Tracer File Location:\n"
                f"{PATHS.PROJECT_ROOT / 'packet-tracer' / 'NETSIMX_Network_Design.pkt'}"
            )
            # Load R1 config by default
            self._load_config_file("packet-tracer/configs/R1.cfg", "Edge Router R1")

    def _load_config_file(self, rel_path: str, device_name: str) -> None:
        full_path = PATHS.PROJECT_ROOT / rel_path
        if full_path.exists():
            try:
                content = full_path.read_text(encoding="utf-8")
                self._cfg_viewer.setPlainText(f"! --- {device_name} ({rel_path}) ---\n\n" + content)
            except Exception as exc:
                self._cfg_viewer.setPlainText(f"Error reading configuration file: {exc}")
        else:
            self._cfg_viewer.setPlainText(f"Configuration file not found at: {full_path}")
