"""
NetSimX — JSON Exporter (Member 4)
Exports experiment data to JSON format.
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("JsonExporter")


class JsonExporter:
    """Exports experiment data to JSON files."""

    @staticmethod
    def export_full_experiment(experiment_dict: Dict[str, Any], filepath: str) -> None:
        """
        Exports a complete experiment to JSON.
        experiment_dict: {
            "config": {...},
            "metrics": {...},
            "events": [...],
            "topology": {...}
        }
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        output = {
            "exported_at": datetime.now().isoformat(),
            "source": "NetSimX Python Simulation",
            **experiment_dict
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

        logger.info(f"Experiment exported to {filepath}")

    @staticmethod
    def export_metrics_series(metrics_list: list, filepath: str) -> None:
        """Exports a time-series of metrics snapshots to JSON."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        output = {
            "exported_at": datetime.now().isoformat(),
            "source": "NetSimX Python Simulation",
            "metrics_series": metrics_list,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

        logger.info(f"Metrics series exported to {filepath}")
