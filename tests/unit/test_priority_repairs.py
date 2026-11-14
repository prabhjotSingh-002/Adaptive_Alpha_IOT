"""Targeted host checks; no simulator or phase validation runs."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'host'))
import calibrate

class CalibrationGuardTests(unittest.TestCase):
    def test_seed_required(self):
        with self.assertRaises(ValueError):
            calibrate.load_summaries(Path('/tmp'))

class PairingTests(unittest.TestCase):
    def test_constant_paired_difference(self):
        from analysis import _paired_diff
        out = _paired_diff([1, 100, 1000], [3, 102, 1002])
        self.assertEqual(out['ci_lo'], 2)
        self.assertEqual(out['ci_hi'], 2)

    def test_unmatched_arrays_rejected(self):
        from analysis import _paired_diff
        with self.assertRaises(ValueError):
            _paired_diff([1, 2], [3])
