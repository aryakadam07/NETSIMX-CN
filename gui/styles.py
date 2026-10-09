"""
NetSimX — Central Design System & Qt Stylesheet Module
Provides colors, typography, and reusable QSS styles for the dark charcoal & emerald aesthetic.
"""

# Color Tokens (Charcoal & Emerald palette - NO BLUE)
MAIN_BG = "#151515"          # Deep charcoal main workspace
SIDEBAR_BG = "#101010"       # Darker charcoal sidebar & header
CARD_BG = "#202020"          # Soft charcoal card container
CONTAINER_BG = "#262626"     # Panel & input container background
BORDER_COLOR = "#353535"     # Subtle charcoal grey border
BORDER_FOCUS = "#B8E986"     # Focus border in emerald green

ACCENT_EMERALD = "#B8E986"   # Primary accent (soft emerald green)
ACCENT_ORANGE = "#E9A15B"    # Secondary accent (warm orange)
ACCENT_AMBER = "#F59E0B"     # Warning amber
ACCENT_CORAL = "#EF4444"     # Error / failure coral red
ACCENT_TEAL = "#34D399"      # Soft teal server accent

TEXT_PRIMARY = "#F4F1EB"     # Warm white primary text
TEXT_SECONDARY = "#A5A5A5"   # Muted grey secondary text
TEXT_DARK = "#101010"        # Dark text for bright emerald buttons


def get_application_stylesheet() -> str:
    """Returns application-wide QSS rules."""
    return f"""
    QMainWindow {{
        background-color: {MAIN_BG};
        color: {TEXT_PRIMARY};
    }}
    QWidget {{
        color: {TEXT_PRIMARY};
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }}
    QToolTip {{
        background-color: {CARD_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
    }}
    QScrollBar:vertical {{
        background: {SIDEBAR_BG};
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER_COLOR};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {ACCENT_EMERALD};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {SIDEBAR_BG};
        height: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER_COLOR};
        min-width: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {ACCENT_EMERALD};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    """


def get_card_stylesheet(bg: str = CARD_BG, border: str = BORDER_COLOR) -> str:
    return f"""
    QFrame {{
        background-color: {bg};
        border: 1px solid {border};
        border-radius: 8px;
    }}
    """


def get_groupbox_stylesheet() -> str:
    return f"""
    QGroupBox {{
        color: {ACCENT_EMERALD};
        font-size: 11px;
        font-weight: bold;
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 14px;
        background-color: {CARD_BG};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        background-color: {CARD_BG};
    }}
    """


def get_input_stylesheet() -> str:
    return f"""
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
        background-color: {CONTAINER_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 11px;
    }}
    QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
        border: 1px solid {ACCENT_EMERALD};
    }}
    QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
        border: 1px solid {ACCENT_EMERALD};
        background-color: #2D2D2D;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {CONTAINER_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        selection-background-color: {CARD_BG};
        selection-color: {ACCENT_EMERALD};
    }}
    """


def get_button_stylesheet(bg: str = ACCENT_EMERALD, fg: str = TEXT_DARK) -> str:
    return f"""
    QPushButton {{
        background-color: {bg};
        color: {fg};
        border: none;
        border-radius: 6px;
        padding: 7px 16px;
        font-size: 11px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #D4F4A9;
    }}
    QPushButton:pressed {{
        background-color: #A3D86F;
    }}
    QPushButton:disabled {{
        background-color: #2D2D2D;
        color: {TEXT_SECONDARY};
    }}
    """


def get_secondary_button_stylesheet() -> str:
    return f"""
    QPushButton {{
        background-color: {CONTAINER_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {CARD_BG};
        border-color: {ACCENT_EMERALD};
        color: {ACCENT_EMERALD};
    }}
    QPushButton:pressed {{
        background-color: #1A1A1A;
    }}
    """


def get_danger_button_stylesheet() -> str:
    return f"""
    QPushButton {{
        background-color: {ACCENT_CORAL};
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 7px 16px;
        font-size: 11px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #F87171;
    }}
    QPushButton:pressed {{
        background-color: #DC2626;
    }}
    """


def get_table_stylesheet() -> str:
    return f"""
    QTableWidget, QTableView {{
        background-color: {CARD_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_COLOR};
        gridline-color: {BORDER_COLOR};
        font-size: 11px;
        border-radius: 6px;
    }}
    QHeaderView::section {{
        background-color: {SIDEBAR_BG};
        color: {TEXT_SECONDARY};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {BORDER_COLOR};
        font-weight: bold;
        font-size: 10px;
    }}
    QTableWidget::item {{
        padding: 6px;
    }}
    QTableWidget::item:selected {{
        background-color: {CONTAINER_BG};
        color: {ACCENT_EMERALD};
    }}
    """


def get_text_edit_stylesheet(text_color: str = ACCENT_EMERALD) -> str:
    return f"""
    QTextEdit, QPlainTextEdit {{
        background-color: #121212;
        color: {text_color};
        border: 1px solid {BORDER_COLOR};
        border-radius: 6px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 11px;
        padding: 8px;
    }}
    """
