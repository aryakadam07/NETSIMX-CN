"""
NetSimX — Matplotlib Chart Canvas (Member 4 / Redesign)
Embeds Matplotlib figures into PyQt6 widgets via FigureCanvasQTAgg.
Styled with a dark charcoal & emerald green aesthetic (NO BLUE).
"""

import logging
from typing import List, Tuple, Optional

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

logger = logging.getLogger("Charts")


class MatplotlibCanvas(FigureCanvasQTAgg):
    """
    Reusable embedded Matplotlib canvas.
    Call plot_*() methods to update the chart.
    """

    COLOR_PRIMARY = "#B8E986"   # Muted Emerald Green
    COLOR_SECONDARY = "#E9A15B" # Warm Orange
    COLOR_CRITICAL = "#EF4444"  # Coral Red
    COLOR_TEAL = "#34D399"      # Soft Teal
    BG_FIGURE = "#1A1A1A"
    BG_AXES = "#222222"
    BORDER_COLOR = "#353535"
    TEXT_PRIMARY = "#F4F1EB"
    TEXT_MUTED = "#A5A5A5"

    def __init__(self, width: int = 6, height: int = 3, dpi: int = 90, parent=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._style()

    def _style(self) -> None:
        self.fig.patch.set_facecolor(self.BG_FIGURE)
        self.axes.set_facecolor(self.BG_AXES)
        self.axes.tick_params(colors=self.TEXT_MUTED, labelsize=8)
        self.axes.grid(True, linestyle="--", linewidth=0.5, color=self.BORDER_COLOR, alpha=0.7)
        for spine in self.axes.spines.values():
            spine.set_edgecolor(self.BORDER_COLOR)
        self.axes.title.set_color(self.TEXT_PRIMARY)
        self.axes.title.set_fontsize(10)
        self.axes.title.set_fontweight("bold")
        self.axes.xaxis.label.set_color(self.TEXT_MUTED)
        self.axes.yaxis.label.set_color(self.TEXT_MUTED)

    def clear(self) -> None:
        self.axes.cla()
        self._style()

    def plot_line(self, x: List[float], y: List[float],
                  title: str = "", xlabel: str = "Time (ms)",
                  ylabel: str = "", color: str = COLOR_PRIMARY,
                  label: str = "") -> None:
        """Simple line chart."""
        self.clear()
        if x and y:
            self.axes.plot(x, y, color=color, linewidth=2.0, label=label)
            self.axes.fill_between(x, y, color=color, alpha=0.1)
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel, fontsize=8)
        self.axes.set_ylabel(ylabel, fontsize=8)
        if label:
            self.axes.legend(fontsize=7, facecolor=self.BG_AXES, labelcolor=self.TEXT_PRIMARY, edgecolor=self.BORDER_COLOR)
        self.draw()

    def plot_multi_line(self, series: List[Tuple[List[float], List[float], str, str]],
                        title: str = "", xlabel: str = "Time (ms)",
                        ylabel: str = "") -> None:
        """
        Multi-series line chart.
        series: list of (x_data, y_data, label, color)
        """
        self.clear()
        for x, y, lbl, col in series:
            if x and y:
                self.axes.plot(x, y, color=col, linewidth=1.8, label=lbl)
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel, fontsize=8)
        self.axes.set_ylabel(ylabel, fontsize=8)
        self.axes.legend(fontsize=7, facecolor=self.BG_AXES, labelcolor=self.TEXT_PRIMARY, edgecolor=self.BORDER_COLOR)
        self.draw()

    def plot_bar(self, categories: List[str], values: List[float],
                  title: str = "", ylabel: str = "",
                  color: str = COLOR_PRIMARY) -> None:
        """Bar chart for comparison views."""
        self.clear()
        if categories and values:
            bars = self.axes.bar(categories, values, color=color, width=0.45, edgecolor=self.BORDER_COLOR)
            max_v = max(values) if values else 1.0
            for bar, val in zip(bars, values):
                self.axes.text(bar.get_x() + bar.get_width() / 2,
                               bar.get_height() + max_v * 0.02,
                               f"{val:.2f}", ha="center", va="bottom",
                               color=self.TEXT_PRIMARY, fontsize=8, fontweight="bold")
        self.axes.set_title(title)
        self.axes.set_ylabel(ylabel, fontsize=8)
        self.axes.tick_params(axis="x", labelsize=8)
        self.draw()
