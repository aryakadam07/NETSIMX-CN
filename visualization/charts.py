"""
NetSimX — Matplotlib Chart Canvas (Member 4)
Embeds Matplotlib figures into PyQt6 widgets via FigureCanvasQTAgg.
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

    def __init__(self, width: int = 6, height: int = 3, dpi: int = 90, parent=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._style()

    def _style(self) -> None:
        self.fig.patch.set_facecolor("#1E1E2E")
        self.axes.set_facecolor("#2A2A3E")
        self.axes.tick_params(colors="#CCCCCC", labelsize=8)
        for spine in self.axes.spines.values():
            spine.set_edgecolor("#555577")
        self.axes.title.set_color("#FFFFFF")
        self.axes.xaxis.label.set_color("#AAAACC")
        self.axes.yaxis.label.set_color("#AAAACC")

    def clear(self) -> None:
        self.axes.cla()
        self._style()

    def plot_line(self, x: List[float], y: List[float],
                  title: str = "", xlabel: str = "Time (ms)",
                  ylabel: str = "", color: str = "#4A90D9",
                  label: str = "") -> None:
        """Simple line chart."""
        self.clear()
        self.axes.plot(x, y, color=color, linewidth=1.5, label=label)
        self.axes.set_title(title, fontsize=10)
        self.axes.set_xlabel(xlabel, fontsize=8)
        self.axes.set_ylabel(ylabel, fontsize=8)
        if label:
            self.axes.legend(fontsize=7, facecolor="#2A2A3E", labelcolor="#CCCCCC")
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
            self.axes.plot(x, y, color=col, linewidth=1.5, label=lbl)
        self.axes.set_title(title, fontsize=10)
        self.axes.set_xlabel(xlabel, fontsize=8)
        self.axes.set_ylabel(ylabel, fontsize=8)
        self.axes.legend(fontsize=7, facecolor="#2A2A3E", labelcolor="#CCCCCC")
        self.draw()

    def plot_bar(self, categories: List[str], values: List[float],
                 title: str = "", ylabel: str = "",
                 color: str = "#4A90D9") -> None:
        """Bar chart for comparison views."""
        self.clear()
        bars = self.axes.bar(categories, values, color=color, width=0.5)
        for bar, val in zip(bars, values):
            self.axes.text(bar.get_x() + bar.get_width() / 2,
                           bar.get_height() + max(values) * 0.02,
                           f"{val:.2f}", ha="center", va="bottom",
                           color="#CCCCCC", fontsize=7)
        self.axes.set_title(title, fontsize=10)
        self.axes.set_ylabel(ylabel, fontsize=8)
        self.axes.tick_params(axis="x", labelsize=7)
        self.draw()
