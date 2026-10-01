"""
NetSimX — Traffic Generator (Member 3)
Produces simulated streams of Packet instances matching flow parameters.
"""

from typing import List
from core.packet import Packet, ProtocolType, PacketStatus
from traffic.flow import FlowConfig
from config.settings import TRAFFIC_PRESETS, SIM_DEFAULTS


class TrafficGenerator:
    """Generates synthetic network traffic bursts for simulation experiments."""

    @staticmethod
    def generate_flow(config: FlowConfig, route: List[str]) -> List[Packet]:
        """
        Creates a sequential list of packets for a specified flow configuration.
        Assigns initial creation timestamps based on inter_packet_gap_ms.
        """
        packets: List[Packet] = []
        for i in range(1, config.packet_count + 1):
            pkt_id = f"{config.flow_id}_P{i:04d}"
            creation_time = config.start_time_ms + ((i - 1) * config.inter_packet_gap_ms)

            pkt = Packet(
                packet_id=pkt_id,
                flow_id=config.flow_id,
                source_id=config.source_id,
                destination_id=config.destination_id,
                size_bytes=config.packet_size_bytes,
                protocol=config.protocol,
                ttl=SIM_DEFAULTS.DEFAULT_TTL,
                created_time_ms=creation_time,
                current_node=config.source_id,
                current_hop_index=0,
                route=list(route),
                status=PacketStatus.CREATED
            )
            packets.append(pkt)

        return packets

    @classmethod
    def generate_preset(
        cls,
        preset: str,
        source: str,
        destination: str,
        route: List[str],
        flow_id: str = "FLOW1"
    ) -> List[Packet]:
        """
        Generates packets based on standard traffic level presets:
        LOW (100 pkts), MEDIUM (500 pkts), HIGH (1000 pkts).
        """
        preset_upper = preset.upper()
        if preset_upper == "LOW":
            count = TRAFFIC_PRESETS.LOW_PACKET_COUNT
            gap = 20.0
        elif preset_upper == "MEDIUM":
            count = TRAFFIC_PRESETS.MEDIUM_PACKET_COUNT
            gap = 10.0
        elif preset_upper == "HIGH":
            count = TRAFFIC_PRESETS.HIGH_PACKET_COUNT
            gap = 2.0  # High stress rate, triggering congestion
        else:
            count = 100
            gap = 20.0

        config = FlowConfig(
            flow_id=flow_id,
            source_id=source,
            destination_id=destination,
            packet_count=count,
            inter_packet_gap_ms=gap,
            protocol=ProtocolType.TCP
        )
        return cls.generate_flow(config, route)
