"""
NetSimX — Tests: Analytics / Metrics Calculator (Member 4)
"""

import pytest
from analytics.metrics import MetricsCalculator


class TestPacketLoss:
    def test_normal(self):
        assert MetricsCalculator.packet_loss_percent(100, 10) == pytest.approx(10.0)

    def test_zero_dropped(self):
        assert MetricsCalculator.packet_loss_percent(100, 0) == pytest.approx(0.0)

    def test_all_dropped(self):
        assert MetricsCalculator.packet_loss_percent(100, 100) == pytest.approx(100.0)

    def test_zero_sent(self):
        # Division by zero guard
        assert MetricsCalculator.packet_loss_percent(0, 0) == pytest.approx(0.0)

    def test_over_100_clamped(self):
        # Should never exceed 100%
        result = MetricsCalculator.packet_loss_percent(10, 15)
        assert result <= 100.0


class TestPDR:
    def test_normal(self):
        assert MetricsCalculator.pdr_percent(100, 90) == pytest.approx(90.0)

    def test_zero_sent(self):
        assert MetricsCalculator.pdr_percent(0, 0) == pytest.approx(0.0)

    def test_full_delivery(self):
        assert MetricsCalculator.pdr_percent(200, 200) == pytest.approx(100.0)


class TestThroughput:
    def test_normal(self):
        # 1000 bytes delivered in 1 second
        # throughput = (1000 * 8) / 1_000_000 = 0.008 Mbps
        result = MetricsCalculator.throughput_mbps(1000, 1.0)
        assert result == pytest.approx(0.008, rel=1e-3)

    def test_zero_duration(self):
        assert MetricsCalculator.throughput_mbps(1000, 0.0) == pytest.approx(0.0)

    def test_zero_bytes(self):
        assert MetricsCalculator.throughput_mbps(0, 1.0) == pytest.approx(0.0)

    def test_high_throughput(self):
        # 12_500_000 bytes in 1 second = 100 Mbps
        result = MetricsCalculator.throughput_mbps(12_500_000, 1.0)
        assert result == pytest.approx(100.0, rel=1e-3)


class TestAverageLatency:
    def test_normal(self):
        latencies = [10.0, 20.0, 30.0]
        assert MetricsCalculator.average_latency_ms(latencies) == pytest.approx(20.0)

    def test_empty_list(self):
        assert MetricsCalculator.average_latency_ms([]) == pytest.approx(0.0)

    def test_single_value(self):
        assert MetricsCalculator.average_latency_ms([42.5]) == pytest.approx(42.5)


class TestJitter:
    def test_normal(self):
        # |20-10| + |10-20| = 10 + 10, mean = 10
        latencies = [10.0, 20.0, 10.0]
        result = MetricsCalculator.jitter_ms(latencies)
        assert result == pytest.approx(10.0)

    def test_less_than_two(self):
        assert MetricsCalculator.jitter_ms([]) == pytest.approx(0.0)
        assert MetricsCalculator.jitter_ms([5.0]) == pytest.approx(0.0)

    def test_constant_latency(self):
        # No variation → jitter = 0
        assert MetricsCalculator.jitter_ms([15.0, 15.0, 15.0]) == pytest.approx(0.0)


class TestNetworkUtilization:
    def test_normal(self):
        depths = {"L1": 25, "L2": 50}
        caps   = {"L1": 50, "L2": 50}
        # L1=50%, L2=100% → avg=75%
        result = MetricsCalculator.network_utilization_percent(depths, caps)
        assert result == pytest.approx(75.0)

    def test_empty(self):
        assert MetricsCalculator.network_utilization_percent({}, {}) == pytest.approx(0.0)

    def test_missing_capacity_uses_default(self):
        depths = {"L1": 25}
        caps   = {}
        # default cap = 50, 25/50 = 50%
        result = MetricsCalculator.network_utilization_percent(depths, caps)
        assert result == pytest.approx(50.0)


class TestFromSimStats:
    """Tests MetricsCalculator.from_sim_stats() using a mock stats object."""

    class MockStats:
        packets_sent = 500
        packets_delivered = 450
        packets_dropped = 50
        total_latency_ms = 9000.0   # 9000ms / 450 = 20ms avg
        total_hops = 1350           # 1350 / 450 = 3 avg hops

        @property
        def pdr_percent(self):
            return (self.packets_delivered / self.packets_sent) * 100

        @property
        def plr_percent(self):
            return (self.packets_dropped / self.packets_sent) * 100

        @property
        def average_delay_ms(self):
            return self.total_latency_ms / self.packets_delivered

        @property
        def average_hops(self):
            return self.total_hops / self.packets_delivered

    def test_basic(self):
        result = MetricsCalculator.from_sim_stats(self.MockStats(), duration_ms=10000)
        assert result["packets_sent"] == 500
        assert result["packets_delivered"] == 450
        assert result["packets_dropped"] == 50
        assert result["pdr_percent"] == pytest.approx(90.0)
        assert result["plr_percent"] == pytest.approx(10.0)
        assert result["avg_latency_ms"] == pytest.approx(20.0)
        assert result["avg_hops"] == pytest.approx(3.0)

    def test_zero_sent(self):
        class ZeroStats:
            packets_sent = 0
            packets_delivered = 0
            packets_dropped = 0
            total_latency_ms = 0.0
            total_hops = 0
            pdr_percent = 0.0
            plr_percent = 0.0
            average_delay_ms = 0.0
            average_hops = 0.0

        result = MetricsCalculator.from_sim_stats(ZeroStats())
        assert result["pdr_percent"] == pytest.approx(0.0)
        assert result["throughput_mbps"] == pytest.approx(0.0)
