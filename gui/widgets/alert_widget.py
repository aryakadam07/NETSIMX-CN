"""
NetSimX — Alert Widget (Member 4)
Scrollable list of timestamped alert messages.
"""

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class AlertWidget(QWidget):
    """Displays a scrollable alert/event log."""

    MAX_ALERTS = 50

    LEVEL_STYLES = {
        "info":     "color: #6699CC; background: #252535; border-left: 3px solid #4466AA;",
        "warning":  "color: #FFAA33; background: #2A2510; border-left: 3px solid #FF8800;",
        "critical": "color: #FF5555; background: #2A1010; border-left: 3px solid #CC2222;",
        "success":  "color: #55CC77; background: #101A10; border-left: 3px solid #338833;",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._alerts = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: #1A1A2A; }"
        )

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(4, 4, 4, 4)
        self._container_layout.setSpacing(3)
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
        label.setStyleSheet(f"QLabel {{ {style} padding: 4px 6px; border-radius: 3px; }}")

        # Insert before stretch (index = count - 1)
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
