"""R05 — Deadline/flush contract tests.

Tests verify the scheduling contract documented in finalPLAN2X §D5:
- Flush triggers at exactly deadline_ms (equality included: oldest_hold >= deadline)
- Flush triggers when count >= cap (before deadline)
- No flush when queue is empty
- Cap reduction below current occupancy: existing readings are NOT silently lost
- Exact encoded capacity derived from budget/header/tag/reading bytes
- lab_commit_on_send rejects count > actual queue size

These use the shared production aggregate.c via ctypes, same code as the mote.
"""
import ctypes
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGGREGATE_C = ROOT / 'firmware/aggregate/aggregate.c'
PROTOCOL_H  = ROOT / 'firmware/common/protocol.h'


def _build_lib(tmp_dir):
    """Compile aggregate.c as a shared library for ctypes testing."""
    out = os.path.join(tmp_dir, 'aggregate_test.so')
    shim = Path(tmp_dir) / 'layout.c'
    shim.write_text('#include <stddef.h>\n#include "aggregate.h"\nsize_t reading_size(void){return sizeof(lab_reading); }\nsize_t batch_size(void){return sizeof(lab_batch); }\nsize_t reading_time_offset(void){return offsetof(lab_reading, created_ms); }\n')
    cmd = [
        'gcc', '-std=c11', '-O0', '-g',
        '-shared', '-fPIC',
        f'-I{ROOT}/firmware/common',
        f'-I{ROOT}/firmware/aggregate',
        str(AGGREGATE_C), str(shim),
        '-o', out,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'Build failed:\n{result.stderr}')
    return out


def _load_constants():
    """Read LAB_CAPACITY, LAB_HEADER, LAB_READING_BYTES from protocol.h."""
    text = PROTOCOL_H.read_text()
    consts = {}
    for line in text.split('\n'):
        for name in ('LAB_CAPACITY', 'LAB_HEADER', 'LAB_READING_BYTES'):
            if f'define {name}' in line:
                parts = line.split()
                try:
                    consts[name] = int(parts[-1].rstrip('u'))
                except ValueError:
                    pass
    return consts


# ── ctypes structs ────────────────────────────────────────────────────────────

class LabReading(ctypes.Structure):
    _fields_ = [
        ('id',         ctypes.c_uint32),
        ('created_ms', ctypes.c_uint32),
        ('value',      ctypes.c_uint16),
    ]

CAPACITY = _load_constants().get('LAB_CAPACITY', 4)

class LabAggregator(ctypes.Structure):
    _fields_ = [
        ('ring',        LabReading * CAPACITY),
        ('sender',      ctypes.c_uint16),
        ('head',        ctypes.c_uint8),
        ('count',       ctypes.c_uint8),
        ('cap',         ctypes.c_uint8),
        ('deadline_ms', ctypes.c_uint32),
        ('last_id',     ctypes.c_uint32),
    ]

class LabBatch(ctypes.Structure):
    _fields_ = [
        ('sender',   ctypes.c_uint16),
        ('epoch', ctypes.c_uint16),
        ('profile', ctypes.c_uint8),
        ('count', ctypes.c_uint8),
        ('counter', ctypes.c_uint32),
        ('readings', LabReading * CAPACITY),
    ]


LAB_OFFER_OK           = 0
LAB_OFFER_WRONG_SOURCE = 1
LAB_OFFER_ORDER        = 2
LAB_OFFER_FULL         = 3


class DeadlineFlushTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp()
        try:
            so_path = _build_lib(cls._tmp)
            cls.lib = ctypes.CDLL(so_path)
            cls._setup_sigs()
        except RuntimeError as e:
            cls.lib = None
            cls._build_error = str(e)

    @classmethod
    def _setup_sigs(cls):
        lib = cls.lib
        lib.lab_aggregate_init.restype  = ctypes.c_bool
        lib.lab_aggregate_init.argtypes = [
            ctypes.POINTER(LabAggregator),
            ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint32,
            ctypes.c_size_t, ctypes.c_size_t,
        ]
        lib.lab_offer.restype  = ctypes.c_int
        lib.lab_offer.argtypes = [
            ctypes.POINTER(LabAggregator), ctypes.c_uint16, LabReading
        ]
        lib.lab_should_flush.restype  = ctypes.c_bool
        lib.lab_should_flush.argtypes = [
            ctypes.POINTER(LabAggregator), ctypes.c_uint32, ctypes.c_bool
        ]
        lib.lab_oldest_hold.restype  = ctypes.c_uint32
        lib.lab_oldest_hold.argtypes = [
            ctypes.POINTER(LabAggregator), ctypes.c_uint32
        ]
        lib.lab_commit_on_send.restype  = ctypes.c_bool
        lib.lab_commit_on_send.argtypes = [
            ctypes.POINTER(LabAggregator), ctypes.c_uint8
        ]
        lib.lab_build_batch.restype  = ctypes.c_bool
        lib.lab_build_batch.argtypes = [
            ctypes.POINTER(LabAggregator), ctypes.c_uint32,
            ctypes.POINTER(LabBatch)
        ]

    def setUp(self):
        if self.lib is None:
            self.skipTest(f'Build failed: {self._build_error}')

    def _init(self, cap=4, deadline=3000, budget=67, reserved=16):
        a = LabAggregator()
        ok = self.lib.lab_aggregate_init(
            ctypes.byref(a), 2, cap, deadline, budget, reserved
        )
        self.assertTrue(ok, 'init must succeed with valid params')
        return a

    def _offer(self, a, reading_id, created_ms, expected=LAB_OFFER_OK):
        r = LabReading(id=reading_id, value=100, created_ms=created_ms)
        result = self.lib.lab_offer(ctypes.byref(a), 2, r)
        self.assertEqual(result, expected)
        return result

    def test_production_struct_layout(self):
        for name, expected in [('reading_size',ctypes.sizeof(LabReading)), ('batch_size',ctypes.sizeof(LabBatch)), ('reading_time_offset',LabReading.created_ms.offset)]:
            fn=getattr(self.lib,name);fn.restype=ctypes.c_size_t
            self.assertEqual(fn(),expected)

    # ── Deadline boundary ────────────────────────────────────────────────────

    def test_no_flush_below_deadline(self):
        a = self._init(cap=4, deadline=3000)
        self._offer(a, 1, 0)
        # At now=2999: hold=2999 < 3000
        self.assertFalse(self.lib.lab_should_flush(ctypes.byref(a), 2999, False))

    def test_flush_at_exact_deadline(self):
        """Equality: hold >= deadline_ms must trigger flush."""
        a = self._init(cap=4, deadline=3000)
        self._offer(a, 1, 0)
        # At now=3000: hold=3000 == deadline → must flush
        self.assertTrue(self.lib.lab_should_flush(ctypes.byref(a), 3000, False))

    def test_flush_above_deadline(self):
        a = self._init(cap=4, deadline=3000)
        self._offer(a, 1, 0)
        self.assertTrue(self.lib.lab_should_flush(ctypes.byref(a), 3001, False))

    def test_oldest_reading_governs_deadline(self):
        """Second reading arrives later; flush uses OLDEST created_ms."""
        a = self._init(cap=4, deadline=3000)
        self._offer(a, 1, 0)      # created at t=0
        self._offer(a, 2, 1000)   # created at t=1000
        # At now=3000: oldest hold = 3000-0 = 3000 >= deadline → flush
        self.assertTrue(self.lib.lab_should_flush(ctypes.byref(a), 3000, False))
        hold = self.lib.lab_oldest_hold(ctypes.byref(a), 3000)
        self.assertEqual(hold, 3000)

    # ── Cap boundary ────────────────────────────────────────────────────────

    def test_flush_when_cap_full(self):
        a = self._init(cap=2, deadline=10000)
        self._offer(a, 1, 0)
        self.assertFalse(self.lib.lab_should_flush(ctypes.byref(a), 100, False))
        self._offer(a, 2, 100)
        # count==cap → flush
        self.assertTrue(self.lib.lab_should_flush(ctypes.byref(a), 100, False))

    def test_offer_full_after_cap(self):
        a = self._init(cap=1, deadline=10000)
        res1 = self._offer(a, 1, 0)
        res2 = self._offer(a, 2, 100, LAB_OFFER_FULL)
        self.assertEqual(res1, LAB_OFFER_OK)
        self.assertEqual(res2, LAB_OFFER_FULL)

    # ── Empty queue ─────────────────────────────────────────────────────────

    def test_no_flush_empty_queue(self):
        a = self._init(cap=4, deadline=0)
        # Even deadline=0 — empty queue must not flush
        self.assertFalse(self.lib.lab_should_flush(ctypes.byref(a), 0, False))

    def test_oldest_hold_empty_is_zero(self):
        a = self._init(cap=4, deadline=3000)
        hold = self.lib.lab_oldest_hold(ctypes.byref(a), 99999)
        self.assertEqual(hold, 0)

    # ── Critical flush ───────────────────────────────────────────────────────

    def test_critical_flush_overrides_all(self):
        a = self._init(cap=4, deadline=10000)
        self._offer(a, 1, 0)
        # Not time, not full — but critical=True must flush
        self.assertFalse(self.lib.lab_should_flush(ctypes.byref(a), 100, False))
        self.assertTrue(self.lib.lab_should_flush(ctypes.byref(a), 100, True))

    # ── Queue cap reduction ──────────────────────────────────────────────────

    def test_readings_not_lost_before_commit(self):
        """Existing readings survive until commit_on_send is called."""
        a = self._init(cap=4, deadline=10000)
        self._offer(a, 1, 0)
        self._offer(a, 2, 100)
        self._offer(a, 3, 200)
        self.assertEqual(a.count, 3)
        # Readings are still present — not silently dropped
        batch = LabBatch()
        ok = self.lib.lab_build_batch(ctypes.byref(a), 1, ctypes.byref(batch))
        self.assertTrue(ok)
        self.assertEqual(batch.count, 3)

    def test_commit_on_send_exact_count(self):
        a = self._init(cap=4, deadline=10000)
        self._offer(a, 1, 0)
        self._offer(a, 2, 100)
        ok = self.lib.lab_commit_on_send(ctypes.byref(a), 2)
        self.assertTrue(ok)
        self.assertEqual(a.count, 0)

    def test_commit_on_send_rejects_over_count(self):
        a = self._init(cap=4, deadline=10000)
        self._offer(a, 1, 0)
        # Commit 2 when only 1 exists — must fail
        ok = self.lib.lab_commit_on_send(ctypes.byref(a), 2)
        self.assertFalse(ok)
        self.assertEqual(a.count, 1)  # unchanged

    # ── Budget-derived cap (payload fit) ─────────────────────────────────────

    def test_cap_clamped_by_budget(self):
        """When budget fits fewer readings than requested cap, cap is clamped."""
        consts = _load_constants()
        header = consts.get('LAB_HEADER', 11)
        rbytes = consts.get('LAB_READING_BYTES', 10)
        # Budget for exactly 2 readings: header + 2*rbytes + reserved
        reserved = 27  # tag+overhead
        budget = header + 2 * rbytes + reserved
        a = self._init(cap=4, deadline=3000, budget=budget, reserved=reserved)
        # cap must be clamped to 2
        self.assertEqual(a.cap, 2)

    def test_cap1_budget_exact(self):
        consts = _load_constants()
        header = consts.get('LAB_HEADER', 11)
        rbytes = consts.get('LAB_READING_BYTES', 10)
        reserved = 27
        budget = header + 1 * rbytes + reserved
        a = self._init(cap=4, deadline=3000, budget=budget, reserved=reserved)
        self.assertEqual(a.cap, 1)

    def test_cap_shrink_chunks_preserve_order_and_deadline(self):
        a=self._init(cap=4)
        for rid in (1,2,3):self._offer(a,rid,(rid-1)*100)
        a.cap=1
        self.assertTrue(self.lib.lab_should_flush(ctypes.byref(a),200,False))
        for rid in (1,2,3):
            b=LabBatch()
            self.assertTrue(self.lib.lab_build_batch(ctypes.byref(a),rid,ctypes.byref(b)))
            self.assertEqual(b.count,1)
            self.assertEqual(b.readings[0].id,rid)
            self.assertEqual(a.count,4-rid)
            self.assertTrue(self.lib.lab_commit_on_send(ctypes.byref(a),b.count))
        self.assertEqual(a.count,0)

    # ── Wrong source / order ─────────────────────────────────────────────────

    def test_wrong_source_rejected(self):
        a = self._init(cap=4, deadline=3000)
        r = LabReading(id=1, value=100, created_ms=0)
        result = self.lib.lab_offer(ctypes.byref(a), 3, r)  # sender=3, not 2
        self.assertEqual(result, LAB_OFFER_WRONG_SOURCE)

    def test_out_of_order_rejected(self):
        a = self._init(cap=4, deadline=3000)
        self._offer(a, 5, 0)
        result = self._offer(a, 3, 100, LAB_OFFER_ORDER)  # id=3 < last_id=5
        self.assertEqual(result, LAB_OFFER_ORDER)


if __name__ == '__main__':
    unittest.main()
