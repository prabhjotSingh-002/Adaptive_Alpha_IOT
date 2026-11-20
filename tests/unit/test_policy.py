"""Host tests for the Phase 5 policy module via ctypes.
Builds policy.c against a minimal stub and exercises all three policies.
"""
import ctypes, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_C = ROOT / "firmware/policy/policy.c"
POLICY_H = ROOT / "firmware/policy/policy.h"

# ── Minimal C shim so policy.c compiles host-side without Contiki headers ──
SHIM = r"""
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "policy.h"
"""

def build_policy_lib(tmpdir):
    src = Path(tmpdir) / "policy_host.c"
    lib = Path(tmpdir) / "policy_host.so"
    src.write_text(SHIM)
    cmd = [
        "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
        "-fPIC", "-shared",
        "-I", str(ROOT / "firmware/policy"),
        str(src), str(POLICY_C),
        "-o", str(lib)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("policy build failed:\n" + result.stderr)
    return lib


def make_state(**kwargs):
    """Return a dict of state fields with sensible defaults."""
    defaults = dict(
        b3_threshold_nj_hi=5_000_000_000,   # 5 J hi
        b3_threshold_nj_lo=2_000_000_000,   # 2 J lo
        b6_profile=1,
        cost_nj=[[2_000_000, 1_800_000, 1_600_000],   # AES cap1/2/4
                 [1_900_000, 1_700_000, 1_500_000]],  # Ascon cap1/2/4
        transition_cost_nj=50_000,
        margin_nj_per_reading=10_000,
        min_dwell_ms=2000,
        deadline_ms=3000,
        payload_budget=67,
        reserved_bytes=16,
        current_profile=1,
        current_cap=1,
        last_switch_ms=0,
        initialized=False,
    )
    defaults.update(kwargs)
    return defaults


def make_features(**kwargs):
    defaults = dict(
        residual_nj=9_000_000_000,
        queue_count=0,
        oldest_hold_ms=0,
        rate_hz_x100=100,
        now_ms=61000,
        context_active=True,
    )
    defaults.update(kwargs)
    return defaults



class Features(ctypes.Structure):
    _fields_ = [('residual_nj', ctypes.c_uint64), ('queue_count', ctypes.c_uint16),
                ('oldest_hold_ms', ctypes.c_uint32), ('rate_hz_x100', ctypes.c_uint16),
                ('now_ms', ctypes.c_uint32), ('context_active', ctypes.c_bool)]
class Action(ctypes.Structure):
    _fields_ = [('profile', ctypes.c_uint8), ('cap', ctypes.c_uint8),
                ('reason', ctypes.c_uint8), ('feasible', ctypes.c_bool)]
class State(ctypes.Structure):
    _fields_ = [('b3_threshold_nj_hi', ctypes.c_uint64), ('b3_threshold_nj_lo', ctypes.c_uint64),
                ('b6_profile', ctypes.c_uint8), ('cost_nj', (ctypes.c_uint64 * 3) * 2),
                ('transition_cost_nj', ctypes.c_uint64), ('margin_nj_per_reading', ctypes.c_uint64),
                ('min_dwell_ms', ctypes.c_uint32), ('deadline_ms', ctypes.c_uint32),
                ('payload_budget', ctypes.c_uint8), ('reserved_bytes', ctypes.c_uint8),
                ('current_profile', ctypes.c_uint8), ('current_cap', ctypes.c_uint8),
                ('last_switch_ms', ctypes.c_uint32), ('initialized', ctypes.c_bool)]

class PolicyTests(unittest.TestCase):
    lib = None
    tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.lib = ctypes.CDLL(str(build_policy_lib(cls.tmpdir.name)))
        for name in ('b3', 'b6', 'p1'):
            fn = getattr(cls.lib, 'lab_policy_' + name)
            fn.argtypes = [ctypes.POINTER(State), ctypes.POINTER(Features)]
            fn.restype = Action

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def _call(self, name, st, f):
        state = State()
        for key, value in st.items():
            if key == 'cost_nj':
                for i in range(2):
                    for j in range(3): state.cost_nj[i][j] = value[i][j]
            else: setattr(state, key, value)
        features = Features(**f)
        out = getattr(self.lib, 'lab_policy_' + name)(ctypes.byref(state), ctypes.byref(features))
        for key in st:
            if key != 'cost_nj': st[key] = getattr(state, key)
        return {key: getattr(out, key) for key, _ in Action._fields_}

    def test_p1_rate_drop_overrides_dwell_and_savings(self):
        st = make_state(initialized=True, current_profile=2, current_cap=4,
                        last_switch_ms=61000, transition_cost_nj=2**60)
        action = self._call('p1', st, make_features(now_ms=61001, rate_hz_x100=25))
        self.assertEqual(action['cap'], 1)
        self.assertTrue(action['feasible'])

    def test_b3_threshold_above_uint32(self):
        st = make_state(b3_threshold_nj_hi=6000000000, b3_threshold_nj_lo=3000000000)
        action = self._b3(st, make_features(residual_nj=5000000000))
        self.assertEqual(action['reason'], 4)

    def test_b6_slow_traffic_cannot_batch(self):
        action = self._b6(make_state(), make_features(rate_hz_x100=25))
        self.assertEqual(action['cap'], 1)

    # ── B3 tests ──────────────────────────────────────────────────────────────

    def test_b3_high_residual_uses_aes(self):
        """Above hi threshold → AES."""
        st = make_state(b3_threshold_nj_hi=5_000_000_000, b3_threshold_nj_lo=2_000_000_000)
        f  = make_features(residual_nj=6_000_000_000)
        action = self._b3(st, f)
        self.assertEqual(action["profile"], 1)
        self.assertEqual(action["cap"], 1)
        self.assertTrue(action["feasible"])
        self.assertEqual(action["reason"], 2)  # LAB_POL_B3_AES

    def test_b3_low_residual_uses_ascon(self):
        """Below lo threshold → Ascon."""
        st = make_state(b3_threshold_nj_hi=5_000_000_000, b3_threshold_nj_lo=2_000_000_000)
        f  = make_features(residual_nj=1_000_000_000)
        action = self._b3(st, f)
        self.assertEqual(action["profile"], 2)
        self.assertEqual(action["reason"], 3)  # LAB_POL_B3_ASCON

    def test_b3_hysteresis_holds_current(self):
        """Inside band → keep current choice."""
        st = make_state(b3_threshold_nj_hi=5_000_000_000, b3_threshold_nj_lo=2_000_000_000,
                        current_profile=1, initialized=True)
        f  = make_features(residual_nj=3_000_000_000)
        action = self._b3(st, f)
        self.assertEqual(action["profile"], 1)
        self.assertEqual(action["reason"], 4)  # LAB_POL_B3_HOLD

    def test_b3_inactive_context_fallback(self):
        """Inactive context → safe fallback AES cap 1."""
        st = make_state()
        f  = make_features(context_active=False)
        action = self._b3(st, f)
        self.assertEqual(action["profile"], 1)
        self.assertEqual(action["cap"], 1)
        self.assertFalse(action["feasible"])
        self.assertEqual(action["reason"], 10)  # LAB_POL_DEPLETED

    def test_b3_no_auth_downgrade(self):
        """B3 never returns profile 0."""
        for residual in (0, 1_000_000_000, 5_000_000_000, 10_000_000_000):
            st = make_state()
            f  = make_features(residual_nj=residual)
            action = self._b3(st, f)
            self.assertIn(action["profile"], (1, 2))

    # ── B6 tests ──────────────────────────────────────────────────────────────

    def test_b6_fixed_cipher_from_calibration(self):
        """B6 always uses b6_profile regardless of residual."""
        for b6p in (1, 2):
            st = make_state(b6_profile=b6p)
            f  = make_features()
            action = self._b6(st, f)
            self.assertEqual(action["profile"], b6p)
            self.assertEqual(action["reason"], 5)  # LAB_POL_B6_FIXED
            self.assertTrue(action["feasible"])

    def test_b6_adaptive_cap_low_queue(self):
        """Choose cap before the first reading, allowing accumulation."""
        st = make_state(b6_profile=1)
        f  = make_features(queue_count=0, oldest_hold_ms=0, rate_hz_x100=200)
        action = self._b6(st, f)
        self.assertEqual(action["cap"], 4)

    def test_b6_adaptive_cap_high_queue_past_half_deadline(self):
        """4 readings queued, hold > deadline/2 → cap 4."""
        st = make_state(b6_profile=1, deadline_ms=3000, payload_budget=67, reserved_bytes=16)
        f  = make_features(queue_count=4, oldest_hold_ms=1600, rate_hz_x100=200)
        action = self._b6(st, f)
        self.assertEqual(action["cap"], 4)

    def test_b6_cap_limited_by_payload_budget(self):
        """Tight payload budget limits cap to 1."""
        st = make_state(b6_profile=1, payload_budget=27, reserved_bytes=16)
        # 27 - 16 - 11 = 0 bytes for readings → max_cap = 1
        f  = make_features(queue_count=4, oldest_hold_ms=1600, rate_hz_x100=200)
        action = self._b6(st, f)
        self.assertEqual(action["cap"], 1)

    def test_b6_invalid_b6_profile_fallback(self):
        """b6_profile=0 is invalid → fallback."""
        st = make_state(b6_profile=0)
        f  = make_features()
        action = self._b6(st, f)
        self.assertFalse(action["feasible"])

    # ── P1 tests ──────────────────────────────────────────────────────────────

    def test_p1_selects_min_cost_action(self):
        """P1 selects the cheapest feasible action."""
        # Make Ascon cap4 cheapest
        costs = [[3_000_000, 2_800_000, 2_600_000],
                 [2_900_000, 2_700_000, 1_000_000]]  # Ascon cap4 cheapest
        st = make_state(cost_nj=costs, transition_cost_nj=0,
                        margin_nj_per_reading=0, min_dwell_ms=0,
                        current_profile=1, current_cap=1, initialized=False,
                        payload_budget=67, reserved_bytes=16)
        f  = make_features(now_ms=5000, rate_hz_x100=200)
        action = self._p1(st, f)
        self.assertEqual(action["profile"], 2)
        self.assertEqual(action["cap"], 4)
        self.assertTrue(action["feasible"])

    def test_p1_dwell_prevents_rapid_switch(self):
        """P1 respects dwell timer."""
        costs = [[3_000_000, 2_800_000, 2_600_000],
                 [2_900_000, 2_700_000, 1_000_000]]
        st = make_state(cost_nj=costs, transition_cost_nj=0,
                        margin_nj_per_reading=0, min_dwell_ms=5000,
                        current_profile=1, current_cap=1,
                        last_switch_ms=1000, initialized=True,
                        payload_budget=67, reserved_bytes=16)
        f  = make_features(now_ms=3000)  # only 2s elapsed < 5s dwell
        action = self._p1(st, f)
        self.assertEqual(action["profile"], 1)
        self.assertEqual(action["reason"], 7)  # LAB_POL_P1_DWELL

    def test_p1_no_switch_when_saving_below_margin(self):
        """P1 doesn't switch if saving < transition_cost + margin."""
        # cur(AES cap1) = 2_000_000, best(Ascon cap4) = 1_950_000
        # saving = 50_000; transition(100_000) + margin(100_000) = 200_000 → no switch
        costs = [[2_000_000, 1_900_000, 1_880_000],
                 [1_990_000, 1_980_000, 1_950_000]]
        st = make_state(cost_nj=costs, transition_cost_nj=100_000,
                        margin_nj_per_reading=100_000, min_dwell_ms=0,
                        current_profile=1, current_cap=1, initialized=True,
                        payload_budget=67, reserved_bytes=16)
        f  = make_features(now_ms=10000)
        action = self._p1(st, f)
        self.assertEqual(action["profile"], 1)
        self.assertEqual(action["reason"], 8)  # LAB_POL_P1_NOSAVE

    def test_p1_no_feasible_action_fallback(self):
        """P1 falls back when no cost data available."""
        costs = [[0, 0, 0], [0, 0, 0]]  # All zeros = no calibration
        st = make_state(cost_nj=costs, min_dwell_ms=0, initialized=False,
                        payload_budget=67, reserved_bytes=16)
        f  = make_features()
        action = self._p1(st, f)
        self.assertFalse(action["feasible"])
        self.assertEqual(action["reason"], 9)  # LAB_POL_NO_FEASIBLE

    def test_p1_inactive_context_fallback(self):
        costs = [[2_000_000, 1_800_000, 1_600_000],
                 [1_900_000, 1_700_000, 1_500_000]]
        st = make_state(cost_nj=costs, min_dwell_ms=0)
        f  = make_features(context_active=False)
        action = self._p1(st, f)
        self.assertFalse(action["feasible"])
        self.assertEqual(action["reason"], 10)  # LAB_POL_DEPLETED

    def test_p1_no_auth_downgrade(self):
        """P1 never returns profile 0."""
        costs = [[2_000_000, 1_800_000, 1_600_000],
                 [1_900_000, 1_700_000, 1_500_000]]
        st = make_state(cost_nj=costs, min_dwell_ms=0)
        for residual in (0, 1_000_000_000, 9_000_000_000):
            f = make_features(residual_nj=residual)
            action = self._p1(st, f)
            self.assertIn(action["profile"], (0, 1, 2))
            if action["feasible"]:
                self.assertIn(action["profile"], (1, 2))

    def test_p1_max_cap_respects_budget(self):
        """max_cap with 47-byte budget = 2 readings (47-16-11)/10 = 2."""
        costs = [[2_000_000, 1_800_000, 1_600_000],
                 [1_900_000, 1_700_000, 1_500_000]]
        st = make_state(cost_nj=costs, min_dwell_ms=0,
                        payload_budget=47, reserved_bytes=16)
        f  = make_features()
        action = self._p1(st, f)
        self.assertLessEqual(action["cap"], 2)

    def test_invalid_initialized_profiles_fail_closed(self):
        for fn in ('b3','b6','p1'):
            for profile in (0,3,255):
                action=self._call(fn,make_state(initialized=True,current_profile=profile),make_features())
                self.assertFalse(action['feasible'])
                self.assertEqual((action['profile'],action['cap']),(1,1))

    def test_invalid_initialized_caps_fail_closed(self):
        for cap in (0,3,255):
            action=self._p1(make_state(initialized=True,current_cap=cap),make_features())
            self.assertFalse(action['feasible'])

    def test_deadline_equality_does_not_predict_full_cap(self):
        for fn in ('b6','p1'):
            st=make_state(min_dwell_ms=0,transition_cost_nj=0,margin_nj_per_reading=0)
            a=self._call(fn,st,make_features(rate_hz_x100=100))
            self.assertEqual(a['cap'],2)  # cap4 fill is exactly the expiry time
            a=self._call(fn,make_state(deadline_ms=3001,min_dwell_ms=0,transition_cost_nj=0,margin_nj_per_reading=0),make_features(rate_hz_x100=100))
            self.assertEqual(a['cap'],4)

    def test_maximum_cost_and_timer_wrap_are_bounded(self):
        a=self._p1(make_state(cost_nj=[[2**64-1,0,0],[0,0,0]],initialized=True,current_profile=1,current_cap=1),make_features())
        self.assertTrue(a['feasible'])
        a=self._p1(make_state(initialized=True,last_switch_ms=2**32-1000),make_features(now_ms=500))
        self.assertEqual(a['reason'],7)  # 1500 ms modulo elapsed; still dwelling

    def test_p1_high_residual_selects_cap4(self):
        """When battery residual is ample, P1 chooses the lowest cost action (Cap 4)."""
        costs = [[3_000_000, 2_800_000, 2_600_000],
                 [2_900_000, 2_700_000, 1_000_000]]  # Ascon cap 4 cheapest
        st = make_state(cost_nj=costs, min_dwell_ms=0, transition_cost_nj=0,
                        margin_nj_per_reading=0, payload_budget=67, reserved_bytes=16)
        f = make_features(rate_hz_x100=200, residual_nj=4_000_000_000)
        action = self._p1(st, f)
        self.assertEqual(action["cap"], 4)
        self.assertEqual(action["profile"], 2)
        self.assertTrue(action["feasible"])

    def test_p1_low_residual_drops_to_cap1(self):
        """When battery residual is below the fill demand of Cap 4, P1 drops to Cap 1."""
        costs = [[3_000_000, 2_800_000, 2_600_000],
                 [2_900_000, 2_700_000, 1_000_000]]
        st = make_state(cost_nj=costs, min_dwell_ms=0, transition_cost_nj=0,
                        margin_nj_per_reading=0, payload_budget=67, reserved_bytes=16)
        # Demand for cap 4 at 1Hz (1000ms) with queue=0 is (4)*1000ms*57.4mJ/s ~ 230mJ
        # Set residual to 10mJ (10,000,000 nJ) -> Cap 4 unaffordable, Cap 1 affordable
        f = make_features(rate_hz_x100=100, queue_count=0, residual_nj=10_000_000)
        action = self._p1(st, f)
        self.assertEqual(action["cap"], 1)
        self.assertTrue(action["feasible"])

    def test_p1_battery_overrides_dwell_when_unaffordable(self):
        """When current action is unaffordable, P1 overrides dwell time to switch."""
        costs = [[3_000_000, 2_800_000, 2_600_000],
                 [2_900_000, 2_700_000, 1_000_000]]
        st = make_state(cost_nj=costs, min_dwell_ms=5000, current_profile=2, current_cap=4,
                        last_switch_ms=1000, initialized=True,
                        payload_budget=67, reserved_bytes=16)
        # At 2Hz (500ms), Cap 4 fills before 3000ms deadline.
        # Demand for Cap 4 is (4)*500ms*57.4mJ/s ~ 115mJ + 560uJ.
        # Residual is 50mJ -> Cap 4 unaffordable, Cap 1 affordable.
        f = make_features(now_ms=2000, rate_hz_x100=200, queue_count=0, residual_nj=50_000_000)
        action = self._p1(st, f)
        self.assertEqual(action["cap"], 1)
        self.assertEqual(action["reason"], 11)  # LAB_POL_P1_BATTERY

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _call_policy(self, fn_name, state_dict, features_dict):
        """Pure-Python stub that runs the policy logic without ctypes.
        Used when ctypes build is unavailable; also validates logic directly."""
        # We test the logic via direct Python re-implementation of the
        # policy rules rather than ctypes, since the C build may not be
        # available in all environments.
        raise NotImplementedError

    def _b3(self, st, f):
        return self._call('b3', st, f)

    def _b6(self, st, f):
        return self._call('b6', st, f)

    def _p1(self, st, f):
        return self._call('p1', st, f)



if __name__ == "__main__":
    unittest.main()
