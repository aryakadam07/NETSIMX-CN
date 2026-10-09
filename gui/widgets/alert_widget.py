"""
NetSimX — Alert Widget (Member 4 / Redesign)
Scrollable list of timestamped alert messages styled with dark charcoal & emerald accents.
"""

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.styles import CARD_BG, SIDEBAR_BG, TEXT_PRIMARY, ACCENT_EMERALD, ACCENT_ORANGE, ACCENT_CORAL, ACCENT_AMBER


class AlertWidget(QWidget):
    """Displays a scrollable alert/event log in charcoal & emerald theme."""

    MAX_ALERTS = 50

    LEVEL_STYLES = {
        "info":     f"color: {TEXT_PRIMARY}; background: #1C1C1C; border-left: 3px solid #888888;",
        "warning":  f"color: {ACCENT_ORANGE}; background: #262015; border-left: 3px solid {ACCENT_ORANGE};",
        "critical": f"color: {ACCENT_CORAL}; background: #261515; border-left: 3px solid {ACCENT_CORAL};",
        "success":  f"color: {ACCENT_EMERALD}; background: #1B2615; border-left: 3px solid {ACCENT_EMERALD};",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alerts = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {CARD_BG}; }}"
        )

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(4, 4, 4, 4)
        self._container_layout.setSpacing(4)
        self._container_layout.addStretch()

        self._scroll.setWidget(self._container)
        main_layout.addWidget(self._scroll)

    def add_alert(self, message: str, level: str = "info") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{ts}] {message}"

        label = QLabel(full_msg)
        label.setWordWrap(True)
        font = QFont()
        font.setPointSize(8)
        label.setFont(font)

        style = self.LEVEL_STYLES.get(level, self.LEVEL_STYLES["info"])
        label.setStyleSheet(f"QLabel {{ {style} padding: 5px 8px; border-radius: 4px; }}")

        # Insert before stretch
        insert_pos = self._container_layout.count() - 1
        self._container_layout.insertWidget(insert_pos, label)

        self._alerts.append(label)

        # Trim old alerts
        while len(self._alerts) > self.MAX_ALERTS:
            old = self._alerts.pop(0)
            self._container_layout.removeWidget(old)
            old.deleteLater()

        # Scroll to bottom
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def clear_alerts(self) -> None:
        for label in self._alerts:
            self._container_layout.removeWidget(label)
            label.deleteLater()
        self._alerts.clear()
