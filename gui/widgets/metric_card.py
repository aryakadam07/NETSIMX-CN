"""
NetSimX — Metric Card Widget (Member 4)
A styled card displaying a single KPI: title, large value, unit.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MetricCard(QFrame):
    """
    Compact stat card:

    ┌─────────────────┐
    │  Packets Sent   │
    │      4521       │
    │       pkts      │
    └─────────────────┘
    """

    STYLE_NORMAL = (
        "QFrame { background: #2A2A3E; border: 1px solid #444466; border-radius: 8px; }"
    )
    STYLE_WARNING = (
        "QFrame { background: #3A2A1E; border: 1px solid #AA7700; border-radius: 8px; }"
    )
    STYLE_CRITICAL = (
        "QFrame { background: #3A1E1E; border: 1px solid #CC3333; border-radius: 8px; }"
    )

    def __init__(self, title: str, value: str = "—",
                 unit: str = "", parent=None):
        super().__init__(parent)
        self.setMinimumSize(130, 90)
        self.setMaximumSize(200, 110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        # Title
        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(8)
        self._title_label.setFont(title_font)
        self._title_label.setStyleSheet("color: #9999BB; background: transparent; border: none;")

        # Value
        self._value_label = QLabel(value)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self._value_label.setFont(value_font)
        self._value_label.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")

        # Unit
        self._unit_label = QLabel(unit)
        self._unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_font = QFont()
        unit_font.setPointSize(7)
        self._unit_label.setFont(unit_font)
        self._unit_label.setStyleSheet("color: #7777AA; background: transparent; border: none;")

        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)
        layout.addWidget(self._unit_label)

        self.setStyleSheet(self.STYLE_NORMAL)

    def update_value(self, value: str) -> None:
        self._value_label.setText(value)

    def set_unit(self, unit: str) -> None:
        self._unit_label.setText(unit)

    def set_status(self, status: str) -> None:
        """status: 'normal' | 'warning' | 'critical'"""
        if status == "warning":
            self.setStyleSheet(self.STYLE_WARNING)
        elif status == "critical":
            self.setStyleSheet(self.STYLE_CRITICAL)
        else:
            self.setStyleSheet(self.STYLE_NORMAL)
