"""
NetSimX — CSV Exporter (Member 4)
Exports experiment data to CSV format.
"""

import csv
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger("CsvExporter")


class CsvExporter:
    """Exports experiment metrics and events to CSV files."""

    @staticmethod
    def export_metrics(metrics_rows: List[Dict[str, Any]], filepath: str) -> None:
        """
        Exports a list of metrics dicts to CSV.
        metrics_rows: list of dicts with consistent keys.
        """
        if not metrics_rows:
            logger.warning("export_metrics: no data to export")
            return

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(metrics_rows[0].keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(metrics_rows)

        logger.info(f"Metrics exported to {filepath} ({len(metrics_rows)} rows)")

    @staticmethod
    def export_events(events_rows: List[Dict[str, Any]], filepath: str) -> None:
        """Exports event log to CSV."""
        if not events_rows:
            logger.warning("export_events: no data to export")
            return

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(events_rows[0].keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(events_rows)

        logger.info(f"Events exported to {filepath}")

    @staticmethod
    def export_full_experiment(experiment_dict: Dict[str, Any], filepath: str) -> None:
        """
        Exports a complete experiment (config + summary metrics) to a single CSV.
        experiment_dict: {
            "config": {...},
            "metrics": {...},
            "events": [...]
        }
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Config section
            writer.writerow(["=== EXPERIMENT CONFIG ==="])
            config = experiment_dict.get("config", {})
            for key, val in config.items():
                writer.writerow([key, val])
            writer.writerow([])

            # Summary metrics
            writer.writerow(["=== SUMMARY METRICS ==="])
            metrics = experiment_dict.get("metrics", {})
            for key, val in metrics.items():
                writer.writerow([key, val])
            writer.writerow([])

            # Events
            events = experiment_dict.get("events", [])
            if events:
                writer.writerow(["=== EVENTS ==="])
                headers = list(events[0].keys())
                writer.writerow(headers)
                for ev in events:
                    writer.writerow([ev.get(h, "") for h in headers])

        logger.info(f"Full experiment exported to {filepath}")
