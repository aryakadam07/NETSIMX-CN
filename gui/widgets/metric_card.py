"""
NetSimX — Metric Card Widget (Member 4 / Redesign)
A styled KPI card displaying title, large metric value, and unit in charcoal & emerald.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.styles import CARD_BG, BORDER_COLOR, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL


class MetricCard(QFrame):
    """
    Compact KPI stat card:
    ┌─────────────────┐
    │  Packets Sent   │
    │      4521       │
    │       pkts      │
    └─────────────────┘
    """

    STYLE_NORMAL = f"""
    QFrame {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
    }}
    """
    STYLE_WARNING = f"""
    QFrame {{
        background-color: #262015;
        border: 1px solid {ACCENT_ORANGE};
        border-radius: 8px;
    }}
    """
    STYLE_CRITICAL = f"""
    QFrame {{
        background-color: #261515;
        border: 1px solid {ACCENT_CORAL};
        border-radius: 8px;
    }}
    """

    def __init__(self, title: str, value: str = "—",
                 unit: str = "", parent=None):
        super().__init__(parent)
        self.setMinimumSize(125, 88)
        self.setMaximumSize(190, 105)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        # Title
        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(8)
        title_font.setWeight(QFont.Weight.Medium)
        self._title_label.setFont(title_font)
        self._title_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; border: none;")

        # Value
        self._value_label = QLabel(value)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(17)
        value_font.setBold(True)
        self._value_label.setFont(value_font)
        self._value_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent; border: none;")

        # Unit
        self._unit_label = QLabel(unit)
        self._unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_font = QFont()
        unit_font.setPointSize(7)
        self._unit_label.setFont(unit_font)
        self._unit_label.setStyleSheet("color: #777777; background: transparent; border: none;")

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
            self._value_label.setStyleSheet(f"color: {ACCENT_ORANGE}; background: transparent; border: none;")
        elif status == "critical":
            self.setStyleSheet(self.STYLE_CRITICAL)
            self._value_label.setStyleSheet(f"color: {ACCENT_CORAL}; background: transparent; border: none;")
        else:
            self.setStyleSheet(self.STYLE_NORMAL)
            self._value_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent; border: none;")
