import ctypes
import tempfile
import unittest
from test_policy import build_policy_lib

class Rate(ctypes.Structure):
    _fields_=[('intervals',ctypes.c_uint32*8),('sum_ms',ctypes.c_uint64),('last_ms',ctypes.c_uint32),('count',ctypes.c_uint8),('next',ctypes.c_uint8),('seen',ctypes.c_bool)]

class MeasuredRateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.lib=ctypes.CDLL(str(build_policy_lib(cls.tmp.name)))
        cls.lib.lab_rate_observe.argtypes=[ctypes.POINTER(Rate),ctypes.c_uint32]
        cls.lib.lab_rate_get.argtypes=[ctypes.POINTER(Rate),ctypes.c_uint32];cls.lib.lab_rate_get.restype=ctypes.c_uint16
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def observe(self,s,now):self.lib.lab_rate_observe(ctypes.byref(s),now)
    def rate(self,s,now):return self.lib.lab_rate_get(ctypes.byref(s),now)
    def test_startup_staleness_and_resume(self):
        s=Rate();self.assertEqual(self.rate(s,0),0)
        self.observe(s,0);self.assertEqual(self.rate(s,0),0)
        self.observe(s,1000);self.assertEqual(self.rate(s,1000),100)
        self.assertEqual(self.rate(s,3000),100);self.assertEqual(self.rate(s,3001),0)
        self.observe(s,5000);self.assertEqual(self.rate(s,5000),40)
    def test_eight_interval_window_tracks_changed_arrivals(self):
        s=Rate();now=0;self.observe(s,now)
        for _ in range(8):now+=1000;self.observe(s,now)
        self.assertEqual(self.rate(s,now),100)
        for _ in range(8):now+=4000;self.observe(s,now)
        self.assertEqual(s.count,8);self.assertEqual(self.rate(s,now),25)
    def test_clock_wrap_and_duplicate_observation(self):
        s=Rate();self.observe(s,2**32-500);self.observe(s,500)
        self.assertEqual(self.rate(s,500),100)
        self.observe(s,500);self.assertEqual(s.count,1)
    def test_large_discontinuity_reinitializes(self):
        s=Rate();self.observe(s,1000);self.observe(s,2000);self.observe(s,2**31+3000)
        self.assertEqual(s.count,0);self.assertEqual(self.rate(s,s.last_ms),0)
    def test_observed_rate_change_drives_production_b6_cap(self):
        from test_policy import State,Features,Action
        self.lib.lab_policy_b6.argtypes=[ctypes.POINTER(State),ctypes.POINTER(Features)]
        self.lib.lab_policy_b6.restype=Action
        rate=Rate();now=0;self.observe(rate,now)
        state=State();state.b6_profile=2;state.deadline_ms=3000;state.payload_budget=67;state.reserved_bytes=16
        for _ in range(8):now+=500;self.observe(rate,now)
        features=Features(rate_hz_x100=self.rate(rate,now),now_ms=now,context_active=True)
        self.assertEqual(self.lib.lab_policy_b6(ctypes.byref(state),ctypes.byref(features)).cap,4)
        for _ in range(8):now+=4000;self.observe(rate,now)
        features.rate_hz_x100=self.rate(rate,now);features.now_ms=now
        self.assertEqual(self.lib.lab_policy_b6(ctypes.byref(state),ctypes.byref(features)).cap,1)

    def test_p1_reacts_to_rate_drop_and_recovers_with_saved_costs(self):
        import json
        from test_policy import Action, Features, ROOT, State, make_state

        table_path = ROOT / 'results/phase_05/z1-nine-node-20261120/cost-table-v1.json'
        if not table_path.is_file():
            self.skipTest('Saved nine-node calibration is unavailable')
        table = json.loads(table_path.read_text())
        configs = json.loads((ROOT / 'configs/phase5.json').read_text())
        cost_row = ctypes.c_uint64 * 3
        costs = (cost_row * 2)(*(cost_row(*row) for row in table['p1_cost_nj']))
        state = State(**make_state(
            cost_nj=costs, current_profile=1, current_cap=1, initialized=True,
            transition_cost_nj=configs['p1_transition_cost_nj'],
            margin_nj_per_reading=configs['p1_margin_nj'],
            min_dwell_ms=configs['p1_min_dwell_ms'],
        ))
        decide = self.lib.lab_policy_p1
        decide.argtypes = [ctypes.POINTER(State), ctypes.POINTER(Features)]
        decide.restype = Action
        rate = Rate()
        now = 0
        self.observe(rate, now)
        for interval, expected_rate, expected_action in (
            (500, 200, (2, 4)), (4000, 25, (1, 1)), (500, 200, (2, 4)),
        ):
            for _ in range(8):
                now += interval
                self.observe(rate, now)
            measured = self.rate(rate, now)
            self.assertEqual(measured, expected_rate)
            features = Features(rate_hz_x100=measured, now_ms=now, context_active=True)
            action = decide(ctypes.byref(state), ctypes.byref(features))
            self.assertTrue(action.feasible)
            self.assertEqual((action.profile, action.cap), expected_action)
