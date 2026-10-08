"""
NetSimX — Experiment Comparison Engine (Member 4)
Side-by-side analysis of completed experiments.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger("ExperimentComparator")


class ExperimentComparator:
    """Compares metrics across multiple completed experiments."""

    DISPLAY_FIELDS = [
        ("algorithm",       "Algorithm",        ""),
        ("packets_sent",    "Pkts Sent",         ""),
        ("packets_delivered","Pkts Delivered",   ""),
        ("plr_percent",     "Packet Loss",       "%"),
        ("pdr_percent",     "PDR",               "%"),
        ("avg_latency_ms",  "Avg Latency",       "ms"),
        ("jitter_ms",       "Jitter",            "ms"),
        ("throughput_mbps", "Throughput",        "Mbps"),
        ("avg_hops",        "Avg Hops",          ""),
    ]

    def compare(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Returns a list of comparison dicts.
        Each dict has keys: name, algorithm, and metric columns.
        rows: list of dicts each containing experiment + metrics fields.
        """
        if not rows:
            return []

        result = []
        for row in rows:
            entry: Dict[str, Any] = {
                "name": row.get("name", "—"),
                "algorithm": row.get("algorithm", "—"),
                "source": row.get("source", "—"),
                "destination": row.get("destination", "—"),
                "status": row.get("status", "—"),
            }
            # Pull metric fields with safe defaults
            entry["packets_sent"] = row.get("packets_sent", 0)
            entry["packets_delivered"] = row.get("packets_delivered", 0)
            entry["packets_dropped"] = row.get("packets_dropped", 0)
            entry["plr_percent"] = row.get("plr_percent", 0.0)
            entry["pdr_percent"] = row.get("pdr_percent", 0.0)
            entry["avg_latency_ms"] = row.get("avg_latency_ms", 0.0)
            entry["jitter_ms"] = row.get("jitter_ms", 0.0)
            entry["throughput_mbps"] = row.get("throughput_mbps", 0.0)
            entry["avg_hops"] = row.get("avg_hops", 0.0)
            result.append(entry)

        return result

    def get_table_headers(self) -> List[str]:
        return [label for _, label, _ in self.DISPLAY_FIELDS]

    def get_table_rows(self, comparison: List[Dict[str, Any]]) -> List[List[str]]:
        rows = []
        for entry in comparison:
            row = []
            for key, _, unit in self.DISPLAY_FIELDS:
                val = entry.get(key, "—")
                if isinstance(val, float):
                    row.append(f"{val:.2f}{unit}")
                else:
                    row.append(f"{val}{unit}")
            rows.append(row)
        return rows
