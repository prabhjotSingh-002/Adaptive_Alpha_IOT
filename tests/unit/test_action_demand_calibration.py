"""Unit tests for decoupled action demand calibration and forecast bounds."""
import json
from pathlib import Path
import unittest

from forecast_action_demand import expected_batches, forecast_bounds_nj, affordable


class ActionDemandCalibrationTests(unittest.TestCase):

    def setUp(self):
        calib_path = Path("results/phase_05/z1-demand-calibration-20261120/demand_calibration.json")
        self.assertTrue(calib_path.exists(), "Calibration file must exist")
        self.calib = json.loads(calib_path.read_text())

    def test_calibration_structure_and_types(self):
        self.assertEqual(self.calib["schema_version"], 1)
        self.assertEqual(self.calib["calibration_seed"], 223457)
        self.assertEqual(self.calib["window_ms"], 2000)
        
        bg = self.calib["background"]
        self.assertGreater(bg["sample_count"], 500)
        self.assertGreater(bg["median_nj"], 100_000_000)
        self.assertLess(bg["median_nj"], 150_000_000)
        self.assertLessEqual(bg["lower_nj"], bg["median_nj"])
        self.assertGreaterEqual(bg["upper_nj"], bg["median_nj"])

    def test_marginal_packet_costs(self):
        pkt = self.calib["marginal_packet_costs"]
        # Must have caps 1, 2, 4 for profiles 1 and 2
        for prof in (1, 2):
            for cap in (1, 2, 4):
                key = f"{prof}_{cap}"
                self.assertIn(key, pkt)
                entry = pkt[key]
                self.assertGreater(entry["median_nj"], 200_000)
                self.assertLess(entry["median_nj"], 1_000_000)
                self.assertLessEqual(entry["lower_nj"], entry["median_nj"])
                self.assertGreaterEqual(entry["upper_nj"], entry["median_nj"])

    def test_transitions_isolated_cost(self):
        trans = self.calib["transitions"]
        self.assertEqual(trans["1_1"]["median_nj"], 0)
        self.assertEqual(trans["2_2"]["median_nj"], 0)
        # Isolated CPU switch costs are between 6 and 8 microjoules
        self.assertGreater(trans["1_2"]["median_nj"], 6000)
        self.assertLess(trans["1_2"]["median_nj"], 8000)
        self.assertGreater(trans["2_1"]["median_nj"], 6000)
        self.assertLess(trans["2_1"]["median_nj"], 8000)

    def test_queue_projection_batches(self):
        # 1. Cap 1 with 2Hz traffic (500ms): 4 arrivals in 2000ms -> 4 singletons
        batches = expected_batches((), 500, 500, 1, 3000, 2000)
        self.assertEqual(batches, (1, 1, 1, 1))

        # 2. Cap 4 with 2 queued readings and 500ms traffic: 2 queued + 4 new = 6 readings
        # First 4 flush as 1 batch of 4. Remaining 2 stay in queue until deadline.
        batches = expected_batches((500, 0), 500, 500, 4, 3000, 2000)
        self.assertEqual(batches, (4,))

        # 3. Queued shrink: cap decreases below queue occupancy (2 > 1)
        # Backlog drains immediately as 2 singletons, then 4 new arrivals -> 6 singletons total
        batches = expected_batches((500, 0), 500, 500, 1, 3000, 2000)
        self.assertEqual(batches, (1, 1, 1, 1, 1, 1))

    def test_forecast_bounds_and_affordability(self):
        bg = (114_000_000, 115_000_000)
        pkt_costs = {
            (1, 1): (330_000, 350_000),
            (2, 4): (550_000, 580_000),
        }
        transitions = {
            (2, 1): (6900, 7100),
            (2, 2): (0, 0),
        }
        
        # Test candidate 1 with 4 singletons and transition from 2 to 1
        bounds = forecast_bounds_nj(
            background=bg,
            batches=(1, 1, 1, 1),
            packet_costs=pkt_costs,
            current=2,
            candidate=1,
            transitions=transitions
        )
        self.assertIsNotNone(bounds)
        lower, upper = bounds
        expected_lower = 114_000_000 + 4 * 330_000 + 6900
        expected_upper = 115_000_000 + 4 * 350_000 + 7100
        self.assertEqual(lower, expected_lower)
        self.assertEqual(upper, expected_upper)
        
        # Affordability check
        self.assertTrue(affordable(bounds, residual_nj=expected_upper + 1000))
        self.assertFalse(affordable(bounds, residual_nj=expected_lower - 1000))
        self.assertIsNone(affordable(bounds, residual_nj=expected_lower + 100))


if __name__ == "__main__":
    unittest.main()
