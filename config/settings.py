"""
NetSimX — Central Configuration & Simulation Constants
Provides global default parameters, directory paths, and traffic presets.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SimulationDefaults:
    """Default physical and networking constants."""
    DEFAULT_PACKET_SIZE_BYTES: int = 1024       # 1 KB per standard packet
    DEFAULT_BANDWIDTH_MBPS: float = 100.0       # 100 Mbps FastEthernet baseline
    DEFAULT_PROPAGATION_DELAY_MS: float = 10.0   # 10 ms wire latency
    DEFAULT_QUEUE_CAPACITY_PACKETS: int = 50    # Drop-Tail buffer threshold
    DEFAULT_TTL: int = 64                       # IPv4 standard Time-To-Live
    TICK_INTERVAL_MS: float = 50.0              # 20 Hz simulation clock step
    SPEED_MULTIPLIER_DEFAULT: float = 1.0


@dataclass(frozen=True)
class TrafficPresets:
    """Preset packet counts and inter-arrival intervals."""
    LOW_PACKET_COUNT: int = 100
    MEDIUM_PACKET_COUNT: int = 500
    HIGH_PACKET_COUNT: int = 1000
    
    DEFAULT_INTER_PACKET_GAP_MS: float = 20.0   # Interval between packet generation


@dataclass(frozen=True)
class PathConfig:
    """Project directory paths."""
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DB_PATH: Path = DATA_DIR / "db" / "netsimx.db"
    SAMPLE_NETWORKS_DIR: Path = DATA_DIR / "sample_networks"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"


# Global instances for convenient import
SIM_DEFAULTS = SimulationDefaults()
TRAFFIC_PRESETS = TrafficPresets()
PATHS = PathConfig()
